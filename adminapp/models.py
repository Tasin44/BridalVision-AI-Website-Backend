from django.conf import settings
from django.db import models


class Category(models.Model):
    """
    Stores dress categories created by the admin.
    Each category has a name and can hold multiple images.
    """
    category_id = models.AutoField(primary_key=True)   # Auto-incrementing PK
    category_type = models.CharField(
        max_length=100,
        unique=True,           # No duplicate category names
        db_index=True          # Index for fast lookups/filtering
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)       # Updated on every save

    class Meta:
        ordering = ['category_type']   # Default alphabetical ordering
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.category_type


class CategoryImage(models.Model):
    """
    Each Category can have multiple images (one-to-many).
    Using select_related/prefetch_related to avoid N+1 queries.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,        # Delete images when category is deleted
        related_name='images'            # Access via category.images.all()
    )
    image_field = models.ImageField(
        upload_to='category_images/%Y/%m/',  # Organized by year/month
        # e.g. media/category_images/2026/05/dress.jpg
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Composite index: speeds up queries filtering by category + upload date
        indexes = [
            models.Index(fields=['category', 'uploaded_at']),
        ]

    def __str__(self):
        return f"{self.category.category_type} - Image {self.pk}"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    profile_image = models.ImageField(
        upload_to='admin_profile/%Y/%m/',
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AdminProfile({self.user_id})"