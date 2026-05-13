from django.urls import path
from .views import (
    AdminLoginView,
    CategoryListCreateView,
    CategoryDetailView,
    CategoryImageUploadView,
    CategoryImageDeleteView,
    ForgotPasswordView,
    VerifyOtpView,
    ResetPasswordView,
    AdminProfileView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,      # POST refresh token → returns new access token
)

urlpatterns = [
    # --- Admin Authentication ---
    path('login/', AdminLoginView.as_view(), name='admin-login'),
    # POST { "username": "admin@email.com", "password": "..." }
    # Returns: { "access": "...", "refresh": "..." }

    path('token/refresh/', TokenRefreshView.as_view(), name='admin-token-refresh'),
    # POST { "refresh": "..." } → Returns new access token

    # --- Password reset ---
    path('forgot-password/', ForgotPasswordView.as_view(), name='admin-forgot-password'),
    path('verify-otp/', VerifyOtpView.as_view(), name='admin-verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='admin-reset-password'),

    # --- Category CRUD ---
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    # GET  → list all categories with images (cached)
    # POST → create new category { "category_type": "Bridal" }

    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    # GET    → single category detail
    # PATCH  → rename category
    # DELETE → delete category + all its images

    # --- Image Management ---
    path(
        'categories/<int:category_id>/images/',
        CategoryImageUploadView.as_view(),
        name='category-image-upload'
    ),
    # POST (multipart) → upload images to a category
    # Form field: images[] (multiple files)

    path(
        'categories/images/<int:image_id>/',
        CategoryImageDeleteView.as_view(),
        name='category-image-delete'
    ),
    # DELETE → remove a single image

     path('admin/profile/', AdminProfileView.as_view(), name='admin-profile'),
]
