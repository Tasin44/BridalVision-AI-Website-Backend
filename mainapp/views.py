from django.shortcuts import render

# Create your views here.
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny    # Public endpoints — no login needed
from rest_framework.pagination import PageNumberPagination

from aamyproject.mixins import StandardResponseMixin
from adminapp.models import Category, CategoryImage
from adminapp.serializers import CategorySerializer
from .models import UserUploadedImage, GeneratedImage,UserSession
from .serializers import (
    UserImageUploadSerializer,
    UserImageReadSerializer,
    GeneratedImageSerializer,
    SendEmailSerializer,
)

# Import your AI module
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])  # Add project root to path
from geminiaiapp.try_on import VirtualTryOn  # Your AI code — untouched


# ─── Custom Pagination ────────────────────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    """
    Reusable pagination class.
    ?page=1&page_size=5 → first 5 items
    """
    page_size = 10             # Default items per page
    page_size_query_param = 'page_size'  # Allow client to override: ?page_size=5
    max_page_size = 50         # Hard cap to prevent abuse


# ─── Public User Endpoints ────────────────────────────────────────────────────

class UserImageUploadView(APIView,StandardResponseMixin):
    """
    POST /api/user/upload/
    User uploads their own photo for try-on.
    No authentication required.
    Returns: uploaded image ID + a session_key (stored client-side as cookie/localStorage)
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, image_id=None):
        session_key = request.query_params.get('session_key')
        if not session_key:
            return Response(
                {'error': 'session_key query param is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if image_id is not None:
            try:
                instance = UserUploadedImage.objects.get(
                    pk=image_id,
                    session_key=session_key
                )
            except UserUploadedImage.DoesNotExist:
                return Response({'error': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)

            serializer = UserImageReadSerializer(instance, context={'request': request})
            return Response(serializer.data)

        queryset = UserUploadedImage.objects.filter(session_key=session_key)
        serializer = UserImageReadSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        # Generate a UUID session key if not provided
        # Client should send this back in subsequent requests to identify themselves
        session_key = request.data.get('session_key') or str(uuid.uuid4())

        serializer = UserImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save with session_key attached
        instance = serializer.save(session_key=session_key)

        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        image_url = request.build_absolute_uri(instance.image.url)
        if base_url:
            image_url = f"{base_url}{instance.image.url}"

        data = {
            'id': instance.pk,
            'image': image_url,
            'session_key': session_key,  # Client must save this for future requests
            'uploaded_at': instance.uploaded_at,
        }
        return self.success_response(data, "Image uploaded successfully", status_code=status.HTTP_201_CREATED)


class CategoryDressListView(StandardResponseMixin, APIView):
    """
    GET /api/categories/
    Returns all dress categories with their images (from admin dashboard).
    Uses Redis caching + pagination for performance.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cache_key = 'user:categories:list'
        cached_data = cache.get(cache_key)

        if cached_data:
            # Serve from Redis — zero DB queries
            return self.success_response(cached_data, "Categories retrieved successfully")

        # Cache miss: run the optimized query
        # prefetch_related('images') → 2 queries total instead of N+1
        categories = Category.objects.prefetch_related('images').all()

        # Manual pagination over queryset
        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated, many=True, context={'request': request})

        # Build the paginated response dict to cache
        response_data = paginator.get_paginated_response(serializer.data).data

        # Cache for 15 minutes (categories don't change often)
        cache.set(cache_key, response_data, timeout=60 * 15)

        return self.success_response(response_data, "Categories retrieved successfully")


class TryOnView(APIView,StandardResponseMixin):
    """
    POST /api/try-on/
    Core AI endpoint: user selects their uploaded image + a dress image
    → AI generates a try-on result → saved to DB as GeneratedImage.

    Input:
        session_key: str        (from upload step)
        user_image_id: int      (ID of their uploaded photo)
        dress_image_id: int     (ID of the dress CategoryImage)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        session_key = request.query_params.get('session_key')
        if not session_key:
            return Response(
                {'error': 'session_key query param is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        generated = GeneratedImage.objects.filter(
            session_key=session_key
        ).order_by('-created_at')

        if not generated.exists():
            return Response(
                {'error': 'No generated images found for this session.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GeneratedImageSerializer(
            generated,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        session_key = request.data.get('session_key')
        user_image_id = request.data.get('user_image_id')
        dress_image_id = request.data.get('dress_image_id')
        try_count = GeneratedImage.objects.filter(session_key=session_key).count()
        if try_count >= 3:
            return Response(
                {'error': 'You have reached the maximum of 3 virtual try-ons per session.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate required fields
        if not all([session_key, user_image_id, dress_image_id]):
            return Response(
                {'error': 'session_key, user_image_id, and dress_image_id are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch user image — verify it belongs to this session
        try:
            user_img_obj = UserUploadedImage.objects.get(
                pk=user_image_id,
                session_key=session_key
            )
        except UserUploadedImage.DoesNotExist:
            return Response({'error': 'User image not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch dress image — single query with related category
        try:
            dress_img_obj = CategoryImage.objects.select_related('category').get(
                pk=dress_image_id
            )
        except CategoryImage.DoesNotExist:
            return Response({'error': 'Dress image not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get absolute file paths for the AI model
        person_path = user_img_obj.image.path       # e.g. /media/user_uploads/2026/05/photo.jpg
        dress_path = dress_img_obj.image_field.path  # e.g. /media/category_images/2026/05/dress.jpg

        # --- Run your AI code (unchanged) ---
        vto = VirtualTryOn()
        #result_pil = vto.perform_try_on(person_path, dress_path)
        result_pil, ai_error = vto.perform_try_on(person_path, dress_path)

        if result_pil is None:
            return Response(
                #{'error': 'AI try-on failed. Please try again.'},
                {'error': ai_error or 'AI try-on failed. Please upload a clearer photo.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Convert image → Django ContentFile to save in DB/media storage
        buffer = BytesIO()
        if hasattr(result_pil, 'image_bytes'):
            buffer.write(result_pil.image_bytes)
        else:
            try:
                #result_pil.save(buffer, format='JPEG', quality=90)
                result_pil.convert("RGB").save(buffer, format='JPEG', quality=90)
            except TypeError:
                result_pil.save(buffer)
        buffer.seek(0)
        file_name = f"tryon_{session_key[:8]}_{uuid.uuid4().hex[:8]}.jpg"
        image_file = ContentFile(buffer.read(), name=file_name)

        # Save to GeneratedImage model
        generated = GeneratedImage.objects.create(
            session_key=session_key,
            user_image=user_img_obj,
            dress_image=dress_img_obj,
            generated_image=image_file,
        )

        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        generated_url = request.build_absolute_uri(generated.generated_image.url)
        if base_url:
            generated_url = f"{base_url}{generated.generated_image.url}"

        data = {
            'id': generated.pk,
            'generated_image': generated_url,
            'created_at': generated.created_at,
            'session_key': session_key,
        }
        return self.success_response(data, "Try-on successful", status_code=status.HTTP_201_CREATED)


class UserGeneratedImagesView(StandardResponseMixin, APIView):
    """
    GET /api/user/generated/?session_key=<key>
    Returns all AI try-on results for this session (paginated).
    No auth — session_key is the identifier.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        session_key = request.query_params.get('session_key')
        if not session_key:
            return self.error_response(
                message='session_key query param is required.',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Filter by session — uses the DB index on session_key for speed
        # select_related avoids extra queries for FK fields we might need
        queryset = GeneratedImage.objects.filter(
            session_key=session_key
        ).select_related('user_image', 'dress_image')

        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = GeneratedImageSerializer(
            paginated,
            many=True,
            context={'request': request}
        )
        data = paginator.get_paginated_response(serializer.data).data
        return self.success_response(data, "Generated images retrieved successfully")


class SendImageByEmailView(StandardResponseMixin, APIView):
    """
    POST /api/user/send-email/
    User provides generated_image_id + email → receives the image as email attachment.
    No auth required.

    Input: { "generated_image_id": 42, "email": "user@example.com" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        generated_image_id = serializer.validated_data.get('generated_image_id')
        generated_image_ids = serializer.validated_data.get('generated_image_ids')
        if generated_image_ids is None:
            generated_image_ids = [generated_image_id]

        #images = list(GeneratedImage.objects.filter(pk__in=generated_image_ids))
        images = list(
            GeneratedImage.objects.filter(pk__in=generated_image_ids)
            .select_related('dress_image')
        )
        if not images:
            return Response({'error': 'Generated images not found.'}, status=status.HTTP_404_NOT_FOUND)

        found_ids = {img.pk for img in images}
        missing_ids = [img_id for img_id in generated_image_ids if img_id not in found_ids]
        if missing_ids:
            return Response(
                {'error': f'Generated images not found: {missing_ids}.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        # image_links = []
        # for gen_img in images:
        #     if base_url:
        #         image_links.append(f"{base_url}{gen_img.generated_image.url}")
        #     else:
        #         image_links.append(request.build_absolute_uri(gen_img.generated_image.url))

        # from_email = getattr(
        #     settings,
        #     'DEFAULT_FROM_EMAIL',
        #     'BridalVision AI <no-reply@bridalvision.ai>'
        # )

        # links_text = '\n'.join(image_links)
        # body = (
        #     'Dear Customer,\n\n'
        #     'Thank you for using BridalVision AI.\n\n'
        #     'Please find your virtual try-on results at the links below:\n'
        #     f'{links_text}\n\n'
        #     'If you need any help, please reply to this email.\n\n'
        #     'Sincerely,\n'
        #     'BridalVision AI'
        # )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Wedding World <no-reply@weddingworld.de>')

        # # Build dress list for email body
        # dress_lines = []
        # for gen_img in images:
        #     dress = gen_img.dress_image
        #     if dress:
        #         brand = dress.brand_name or ''
        #         name = dress.dress_name or ''
        #         url = dress.web_url or ''
        #         dress_lines.append(f"{brand} {name} {url}".strip())

        # dress_list_text = "\n".join(dress_lines) if dress_lines else "–"

        # body = (
        #     "Liebe Braut,\n\n"
        #     "vielen Dank, dass du unsere Virtual Bridal Fitting Room genutzt hast.\n\n"
        #     "Im Anhang findest du deine virtuellen Anprobe-Ergebnisse. "
        #     "Du hast folgende Kleider anprobiert:\n\n"
        #     f"{dress_list_text}\n\n"
        #     "Wir hoffen, dass diese Ergebnisse deine Vorfreude geweckt haben, "
        #     "diese und noch viele weitere Kleider in unserem wunderschönen Store anzuprobieren. "
        #     "Gerne helfen wir dir dabei, während eines persönlichen Brauttermins bei uns "
        #     "dein Traumkleid zu finden. Vereinbare hier deinen Termin – wir freuen uns darauf, "
        #     "dich schon bald in Oberhausen begrüßen zu dürfen.\n\n"
        #     "Liebe Grüße\n"
        #     "Team Wedding World"
        # )
        APPOINTMENT_URL = getattr(settings, 'APPOINTMENT_URL', 'https://www.weddingworld.de/termin-buchen/terminbuchung-braut')

        dress_lines_html = ""
        for gen_img in images:
            dress = gen_img.dress_image
            if dress:
                brand = dress.brand_name or ''
                name = dress.dress_name or ''
                url = dress.web_url or '#'
                label = f"{brand} {name}".strip() or f"Kleid #{dress.pk}"
                # dress_lines_html += f'<p><a href="{url}">{brand} {name}</a></p>\n'
                if dress.web_url:
                    # web_url present → use it
                    url = dress.web_url
                else:
                    # web_url missing → fallback to dress image_url
                    base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
                    url = (
                        f"{base_url}{dress.image_field.url}"
                        if base_url
                        else request.build_absolute_uri(dress.image_field.url)
                    )

                dress_lines_html += f'<p><a href="{url}">{label}</a></p>\n'

        if not dress_lines_html:
            dress_lines_html = '<p>–</p>'

        html_body = (
            '<p>Liebe Braut,</p>'
            '<p>vielen Dank, dass du unsere Virtual Bridal Fitting Room genutzt hast.</p>'
            '<p>Im Anhang findest du deine virtuellen Anprobe-Ergebnisse. '
            'Du hast folgende Kleider anprobiert:</p>'
            f'{dress_lines_html}'
            '<p>Wir hoffen, dass diese Ergebnisse deine Vorfreude geweckt haben, '
            'diese und noch viele weitere Kleider in unserem wunderschönen Store anzuprobieren. '
            'Gerne helfen wir dir dabei, während eines persönlichen Brauttermins bei uns '
            'dein Traumkleid zu finden. '
            f'<a href="{APPOINTMENT_URL}">Vereinbare hier deinen Termin</a> – '
            'wir freuen uns darauf, dich schon bald in Oberhausen begrüßen zu dürfen.</p>'
            '<p>Liebe Grüße<br>Team Wedding World</p>'
        )

        mail = EmailMessage(
            subject='Deine virtuellen Anprobe-Ergebnisse – Wedding World',
            body=html_body,
            from_email=from_email,
            to=[email],
        )
        mail.content_subtype = "html"  # ← THIS was missing
        # Attach each generated image as JPEG
        for gen_img in images:
            with open(gen_img.generated_image.path, 'rb') as f:
                mail.attach(
                    filename=os.path.basename(gen_img.generated_image.name),
                    content=f.read(),
                    mimetype='image/jpeg',
                )

        mail.send()

        GeneratedImage.objects.filter(pk__in=generated_image_ids).update(
            email_sent_to=email
        )
        # if images:
        #     session_key = images[0].session_key
        #     UserSession.objects.update_or_create(
        #         session_key=session_key,
        #         defaults={'email': email}
        #     )
        if images:
            UserSession.objects.update_or_create(
                session_key=images[0].session_key,
                defaults={'email': email}
            )
        return self.success_response(
            None,
            message=f'Images sent successfully to {email}.'
        )

class CategoryDressListView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.query_params.get('search', '').strip()

        # Don't cache when search is active
        if not search:
            cache_key = 'user:categories:list'
            cached_data = cache.get(cache_key)
            if cached_data:
                return self.success_response(cached_data, "Categories retrieved successfully")

        categories = Category.objects.prefetch_related('images').all()

        if search:
            categories = categories.filter(category_type__icontains=search)

        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated, many=True, context={'request': request})
        response_data = paginator.get_paginated_response(serializer.data).data

        if not search:
            cache.set(cache_key, response_data, timeout=60 * 15)

        return self.success_response(response_data, "Categories retrieved successfully")