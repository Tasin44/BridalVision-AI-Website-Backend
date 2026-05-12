from django.urls import path
from .views import (
    UserImageUploadView,
    CategoryDressListView,
    TryOnView,
    UserGeneratedImagesView,
    SendImageByEmailView,
)

urlpatterns = [
    # POST → user uploads their photo
    # Body: multipart — image file + optional session_key
    path('user/upload/', UserImageUploadView.as_view(), name='user-upload'),
    path('user/upload/<int:image_id>/', UserImageUploadView.as_view(), name='user-upload-detail'),

    # GET → all dress categories with images (cached, paginated)
    # ?page=1&page_size=10
    path('categories/', CategoryDressListView.as_view(), name='category-dress-list'),

    # POST → run AI try-on
    # Body: { "session_key": "...", "user_image_id": 1, "dress_image_id": 2 }
    path('try-on/', TryOnView.as_view(), name='try-on'),

    # GET → all generated images for a session
    # ?session_key=<uuid>&page=1
    path('user/generated/', UserGeneratedImagesView.as_view(), name='user-generated-images'),

    # POST → email a generated image
    # Body: { "generated_image_id": 42, "email": "you@example.com" }
    path('user/send-email/', SendImageByEmailView.as_view(), name='send-email'),
]