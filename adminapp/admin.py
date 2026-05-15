from django.contrib import admin

# Register your models here.
from .models import Category,CategoryImage,AdminProfile

admin.site.register(CategoryImage)
admin.site.register(Category)
admin.site.register(AdminProfile)