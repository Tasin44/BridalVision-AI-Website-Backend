from django.contrib.auth import get_user_model
from django.core.cache import cache       # Redis cache
from django.core.mail import send_mail
from django.shortcuts import render
from django.utils.crypto import get_random_string
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, CategoryImage
from .serializers import (
    CategorySerializer,
    CategoryWriteSerializer,
    CategoryImageUploadSerializer,
    AdminTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)

# Cache key prefix — used to namespace and invalidate category caches
CATEGORY_CACHE_PREFIX = 'categories'
CATEGORY_LIST_CACHE_KEY = 'categories:list:all'
USER_CATEGORY_LIST_CACHE_KEY = 'user:categories:list'
OTP_CACHE_PREFIX = 'admin:otp'
OTP_TTL_SECONDS = 60 * 10


def invalidate_category_cache(category_id=None):
    """
    Helper to invalidate all category-related caches.
    Called whenever data changes (create/update/delete).
    """
    cache.delete(CATEGORY_LIST_CACHE_KEY)  # Always invalidate the full list
    cache.delete(USER_CATEGORY_LIST_CACHE_KEY)
    if category_id:
        # Also invalidate any per-category cache
        cache.delete(f'{CATEGORY_CACHE_PREFIX}:{category_id}')


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /admin/categories/      → List all categories with their images
    POST /admin/categories/      → Create a new category
    Only accessible to authenticated admin users.
    """
    permission_classes = [IsAuthenticated]  # Only logged-in admins

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        """
        prefetch_related('images') solves the N+1 problem:
        Without it: 1 query for categories + N queries for each category's images
        With it: 1 query for categories + 1 query for ALL images = 2 total queries
        """
        return Category.objects.prefetch_related('images').all()

    def get_serializer_class(self):
        # Use read serializer for GET, write serializer for POST
        if self.request.method == 'GET':
            return CategorySerializer
        return CategoryWriteSerializer

    def list(self, request, *args, **kwargs):
        """Override list() to add Redis caching for GET requests."""
        cached = cache.get(CATEGORY_LIST_CACHE_KEY)  # Try Redis first
        if cached:
            return Response(cached)   # Return cached data instantly

        # Cache miss → hit the database
        queryset = self.get_queryset()
        serializer = CategorySerializer(queryset, many=True, context={'request': request})
        data = serializer.data

        cache.set(CATEGORY_LIST_CACHE_KEY, data, timeout=60 * 10)  # Cache 10 min
        return Response(data)

    def perform_create(self, serializer):
        """After creating a category, invalidate the list cache."""
        instance = serializer.save()
        invalidate_category_cache()  # New category → old cache is stale

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        invalidate_category_cache()

        read_serializer = CategorySerializer(instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /admin/categories/<id>/   → Get single category detail
    PUT    /admin/categories/<id>/   → Full update
    PATCH  /admin/categories/<id>/   → Partial update (e.g., just rename)
    DELETE /admin/categories/<id>/   → Delete category + all its images (CASCADE)
    """
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.prefetch_related('images').all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CategorySerializer
        return CategoryWriteSerializer

    def retrieve(self, request, *args, **kwargs):
        """Cache per-category GET responses."""
        pk = self.kwargs['pk']
        cache_key = f'{CATEGORY_CACHE_PREFIX}:{pk}'

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        instance = self.get_object()  # Fetches with prefetch_related
        serializer = CategorySerializer(instance, context={'request': request})
        data = serializer.data

        cache.set(cache_key, data, timeout=60 * 10)
        return Response(data)

    def perform_update(self, serializer):
        """Invalidate cache after update."""
        instance = serializer.save()
        invalidate_category_cache(instance.category_id)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        invalidate_category_cache(instance.category_id)

        read_serializer = CategorySerializer(instance, context={'request': request})
        return Response(read_serializer.data)

    def perform_destroy(self, instance):
        """Invalidate cache before deletion."""
        invalidate_category_cache(instance.category_id)
        instance.delete()  # CASCADE deletes all CategoryImage records too


class CategoryImageUploadView(APIView):
    """
    POST /admin/categories/<category_id>/images/
    Upload one or multiple images to an existing category.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Required to handle file uploads

    def post(self, request, category_id):
        # Fetch the category or return 404
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return Response(
                {'error': 'Category not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 'images' is a list of uploaded files from the request
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'No images provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Bulk create all images in ONE query instead of N individual inserts
        # This is DB-efficient for multiple image uploads
        image_objects = [
            CategoryImage(category=category, image_field=img)
            for img in images
        ]
        CategoryImage.objects.bulk_create(image_objects)  # Single INSERT statement

        # Invalidate cache since category images changed
        invalidate_category_cache(category_id)

        return Response(
            {'message': f'{len(images)} image(s) uploaded successfully.'},
            status=status.HTTP_201_CREATED
        )


class CategoryImageDeleteView(APIView):
    """
    DELETE /admin/categories/images/<image_id>/
    Delete a single image from a category.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, image_id):
        try:
            image = CategoryImage.objects.select_related('category').get(pk=image_id)
            # select_related('category') fetches category in same query (no extra query needed)
        except CategoryImage.DoesNotExist:
            return Response(
                {'error': 'Image not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        category_id = image.category.category_id
        image.delete()
        invalidate_category_cache(category_id)  # Invalidate parent category cache

        return Response(
            {'message': 'Image deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        otp = get_random_string(length=6, allowed_chars='0123456789')
        cache_key = f"{OTP_CACHE_PREFIX}:{user.id}"
        cache.set(cache_key, otp, timeout=OTP_TTL_SECONDS)

        try:
            send_mail(
                subject='Your password reset OTP',
                message=f"Your OTP is: {otp}",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as exc:
            return Response(
                {'error': f'Failed to send OTP email: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({'message': 'OTP sent to email.'}, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response(
                {'error': 'email and otp are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"{OTP_CACHE_PREFIX}:{user.id}"
        cached_otp = cache.get(cache_key)
        if not cached_otp or cached_otp != otp:
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(cache_key)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        new_password = serializer.validated_data['new_password']

        user = request.user
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)