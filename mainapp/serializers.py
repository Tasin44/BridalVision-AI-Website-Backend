from django.conf import settings
from rest_framework import serializers
from .models import UserUploadedImage, GeneratedImage


class UserImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for user image upload."""
    class Meta:
        model = UserUploadedImage
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['uploaded_at']  # Auto-set, not user-supplied


class UserImageReadSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = UserUploadedImage
        fields = ['id', 'image', 'image_url', 'session_key', 'uploaded_at']

    def get_image_url(self, obj):
        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        if base_url:
            return f"{base_url}{obj.image.url}"

        request = self.context.get('request')
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)


class GeneratedImageSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying generated try-on images.
    Shows the generated image + metadata.
    """
    class Meta:
        model = GeneratedImage
        fields = ['id', 'generated_image', 'created_at', 'email_sent_to']


class SendEmailSerializer(serializers.Serializer):
    """
    Input validation for the email-sending endpoint.
    We only need the generated image ID and email address.
    """
    generated_image_id = serializers.IntegerField()
    email = serializers.EmailField()   # Validates email format automatically