from django.contrib import admin

# Register your models here.
from django.contrib import admin

# Register your models here.
from .models import UserUploadedImage,GeneratedImage,UserSession

admin.site.register(UserUploadedImage)
admin.site.register(GeneratedImage)
admin.site.register(UserSession)