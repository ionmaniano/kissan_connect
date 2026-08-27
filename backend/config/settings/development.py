from .base import *


DEBUG = True

SECRET_KEY = "django-insecure-development-only-key"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]


# Development email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
