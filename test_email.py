import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aamyproject.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import traceback

print("Testing email send...")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

try:
    result = send_mail(
        'Test Subject',
        'Test Message',
        settings.DEFAULT_FROM_EMAIL,
        ['mdtm20062@gmail.com'], # test recipient
        fail_silently=False
    )
    print(f"Send mail result: {result}")
except Exception as e:
    print("Email sending failed!")
    traceback.print_exc()

