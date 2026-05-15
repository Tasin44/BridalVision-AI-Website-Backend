from django.db import models

# Create your models here.
from django.db import models


class UserUploadedImage(models.Model):
    """
    Stores images uploaded by users (their own photo for try-on).
    No user auth — identified by a UUID session key instead.
    """
    # session_key = models.CharField(
    #     max_length=64,
    #     db_index=True   # Index for fast lookups by session (used in list queries)
    # )
    session_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True
    )
    image = models.ImageField(upload_to='user_uploads/%Y/%m/')  # Organized storage
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']   # Newest first

    def __str__(self):
        return f"UserImage {self.pk} - session {self.session_key[:8]}"


class GeneratedImage(models.Model):
    """
    Stores the AI-generated try-on result images.
    Links the user's original image + the dress category image used.
    """
    # session_key = models.CharField(
    #     max_length=64,
    #     db_index=True    # Index so we can quickly list all images for a session
    # )
    session_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True
    )
    user_image = models.ForeignKey(
        UserUploadedImage,
        on_delete=models.SET_NULL,   # Keep generated image even if source is deleted
        null=True,
        related_name='generated_images'
    )
    dress_image = models.ForeignKey(
        # Importing here avoids circular imports between apps
        'adminapp.CategoryImage',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_images'
    )
    generated_image = models.ImageField(
        upload_to='generated_images/%Y/%m/'  # AI output stored separately
    )
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent_to = models.EmailField(
        blank=True,
        null=True    # Null if user hasn't requested email yet
    )

    class Meta:
        ordering = ['-created_at']   # Newest first
        indexes = [
            # Composite index for the common query: filter by session + order by date
            models.Index(fields=['session_key', '-created_at']),
        ]

    def __str__(self):
        return f"GeneratedImage {self.pk}"