from django.contrib import admin

# Register your models here.
from django.contrib import admin

# Register your models here.
from .models import UserUploadedImage,GeneratedImage,UserSession
from django.utils.html import format_html

@admin.register(UserUploadedImage)
class UserUploadedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_key', 'uploaded_at')
    search_fields = ('session_key',)

@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'email_sent_to', 'session_key', 'created_at', 'image_preview')
    search_fields = ('email_sent_to', 'session_key')
    list_filter = ('created_at',)
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.generated_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 150px;" />', obj.generated_image.url)
        return ""
    image_preview.short_description = 'Image Preview'

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'email', 'created_at', 'updated_at')
    search_fields = ('email', 'session_key')