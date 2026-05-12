from django.db import models

# Create your models here.
from django.db import models

# aiapp acts as a thin integration layer.
# The AI logic lives in try_on.py / config.py / prompts.py / utils.py (your existing code).
# We store AI job logs here for debugging/monitoring.


class AIJobLog(models.Model):
    """
    Optional: Audit log for every AI try-on call.
    Useful for debugging failures, monitoring usage, and billing.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    session_key = models.CharField(max_length=64, db_index=True)
    user_image_path = models.TextField()    # Path used as input
    dress_image_path = models.TextField()   # Path used as input
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)  # Populated on failure
    model_used = models.CharField(max_length=100, blank=True)  # Track which AI model ran
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_key', 'status']),  # Fast lookup by session + status
        ]

    def __str__(self):
        return f"AIJob {self.pk} [{self.status}]"