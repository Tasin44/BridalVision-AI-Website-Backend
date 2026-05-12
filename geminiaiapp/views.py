from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import AIJobLog
from .serializers import AIJobLogSerializer
from .config import MODEL,available_models,resolution
# from import config  # Your existing config.py


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AIConfigView(APIView):
    """
    GET /aiapp/config/
    Returns current AI model config (admin only).
    Useful for verifying which model + resolution is active.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'current_model': MODEL,
            'available_models': available_models,
            'resolution': resolution,
        })


class AIJobLogListView(APIView):
    """
    GET /aiapp/logs/
    Admin-only view of all AI job logs.
    Paginated for performance.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only query the columns needed — defer heavy text fields if not needed
        logs = AIJobLog.objects.all()

        # Optional filter by status: /aiapp/logs/?status=failed
        status_filter = request.query_params.get('status')
        if status_filter:
            logs = logs.filter(status=status_filter)

        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(logs, request)
        serializer = AIJobLogSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)