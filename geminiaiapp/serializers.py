from rest_framework import serializers
from .models import AIJobLog


class AIJobLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for job logs (admin monitoring)."""
    class Meta:
        model = AIJobLog
        fields = ['id', 'session_key', 'status', 'model_used', 'error_message',
                  'created_at', 'completed_at']
        read_only_fields = fields  # All fields are read-only (logs are system-generated)