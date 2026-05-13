
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Category, CategoryImage, AdminProfile


class CategoryImageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual category images.
    Used nested inside CategorySerializer.
    """
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CategoryImage
        fields = ['id', 'image_url', 'uploaded_at']  # Only expose needed fields

    def get_image_url(self, obj):
        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        if base_url:
            return f"{base_url}{obj.image_field.url}"

        request = self.context.get('request')
        if request is None:
            return obj.image_field.url
        return request.build_absolute_uri(obj.image_field.url)


class CategorySerializer(serializers.ModelSerializer):
    """
    Full category serializer with nested images.
    'images' uses prefetch_related in views to avoid N+1 queries.
    """
    images = CategoryImageSerializer(
        many=True,
        read_only=True   # Images are uploaded separately, not via this serializer
    )

    class Meta:
        model = Category
        fields = ['category_id', 'category_type', 'images', 'created_at', 'updated_at']


class CategoryWriteSerializer(serializers.ModelSerializer):
    """
    Separate write serializer for create/update operations.
    Separating read vs write serializers is a clean pattern.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True,
        allow_empty=True
    )

    class Meta:
        model = Category
        fields = ['category_type', 'images']

    def validate_category_type(self, value):
        # Strip whitespace and capitalize for consistency
        normalized = value.strip().title()

        qs = Category.objects.filter(category_type__iexact=normalized)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Category with this name already exists.')

        return normalized

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        category = Category.objects.create(**validated_data)
        if images:
            CategoryImage.objects.bulk_create([
                CategoryImage(category=category, image_field=image)
                for image in images
            ])
        return category

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if images is not None:
            instance.images.all().delete()
            if images:
                CategoryImage.objects.bulk_create([
                    CategoryImage(category=instance, image_field=image)
                    for image in images
                ])

        return instance


class CategoryImageUploadSerializer(serializers.Serializer):
    """
    Handles uploading multiple images to an existing category.
    Not a ModelSerializer because we handle multiple files manually.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),   # Each item must be a valid image
        allow_empty=False,                # At least one image required
        max_length=20                     # Max 20 images per upload
    )


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Allow login via username or email and return user info in the response."""

    def validate(self, attrs):
        identifier = attrs.get('username')
        password = attrs.get('password')
        User = get_user_model()

        user = None
        if identifier and '@' in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                user = None

        if user is None:
            user = authenticate(
                username=identifier,
                password=password
            )
        else:
            user = authenticate(
                username=user.get_username(),
                password=password
            )

        if not user:
            raise serializers.ValidationError('Invalid login credentials.')

        data = super().validate({
            'username': user.get_username(),
            'password': password,
        })

        data['user'] = {
            'id': user.id,
            'username': user.get_username(),
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        User = get_user_model()
        email = attrs['email']
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        attrs['user'] = user
        return attrs

    def get_reset_payload(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        return uid, token


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6)



from django.contrib.auth import get_user_model

User = get_user_model()


class AdminProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'profile_image',
        ]

    def get_profile_image(self, obj):
        request = self.context.get('request')

        profile = getattr(obj, 'admin_profile', None)
        if profile and profile.profile_image:
            base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
            if base_url:
                return f"{base_url}{profile.profile_image.url}"
            if request:
                return request.build_absolute_uri(profile.profile_image.url)
            return profile.profile_image.url

        return None


class AdminProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'profile_image',
        ]

    def update(self, instance, validated_data):
        profile_image = validated_data.pop('profile_image', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_image is not None:
            profile, _created = AdminProfile.objects.get_or_create(user=instance)
            profile.profile_image = profile_image
            profile.save(update_fields=['profile_image', 'updated_at'])

        return instance