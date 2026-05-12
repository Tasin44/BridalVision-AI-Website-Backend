from django.urls import path
from .views import AIConfigView, AIJobLogListView

urlpatterns = [
    # GET → current AI model configuration (admin only)
    path('config/', AIConfigView.as_view(), name='ai-config'),

    # GET → AI job execution logs (admin only, paginated)
    # ?status=failed → filter by status
    # ?page=2&page_size=20 → paginate
    path('logs/', AIJobLogListView.as_view(), name='ai-job-logs'),
]