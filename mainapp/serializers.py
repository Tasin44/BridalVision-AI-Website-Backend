from django.conf import settings
from rest_framework import serializers
from .models import UserUploadedImage, GeneratedImage


class UserImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for user image upload."""
    class Meta:
        model = UserUploadedImage
        #fields = ['id', 'image', 'uploaded_at']
        fields = ['id', 'image', 'session_key', 'uploaded_at']
        read_only_fields = ['uploaded_at']  # Auto-set, not user-supplied
        extra_kwargs = {
            'session_key': {
                'required': False,
                'allow_null': True,
                'allow_blank': True,
            }
        }


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
    generated_image = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedImage
        fields = ['id', 'generated_image', 'created_at', 'session_key', 'email_sent_to']

    def get_generated_image(self, obj):
        base_url = getattr(settings, 'BASE_URL', '').rstrip('/')
        if base_url:
            return f"{base_url}{obj.generated_image.url}"

        request = self.context.get('request')
        if request is None:
            return obj.generated_image.url
        return request.build_absolute_uri(obj.generated_image.url)


class SendEmailSerializer(serializers.Serializer):
    """
    Input validation for the email-sending endpoint.
    We only need the generated image ID and email address.
    """
    generated_image_id = serializers.IntegerField(required=False)
    generated_image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False
    )
    email = serializers.EmailField()   # Validates email format automatically

    def validate(self, attrs):
        single_id = attrs.get('generated_image_id')
        many_ids = attrs.get('generated_image_ids')

        if not single_id and not many_ids:
            raise serializers.ValidationError(
                'Provide generated_image_id or generated_image_ids.'
            )

        if single_id and many_ids:
            raise serializers.ValidationError(
                'Provide only one of generated_image_id or generated_image_ids.'
            )

        return attrs