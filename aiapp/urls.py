from django.urls import path
from .views import try_on

urlpatterns = [
    path("try-on/", try_on),
]