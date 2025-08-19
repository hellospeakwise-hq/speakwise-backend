"""
Development settings for SpeakWise project.
"""

from .base import *  # Import base settings  # noqa: E402,F403,F401
from .base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE  # noqa: E402

try:
    import debug_toolbar  # noqa: F401
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-development-key-change-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Your Next.js app
    "http://127.0.0.1:3000",
]

# Or for development, you can allow all origins (less secure):
# CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Debug toolbar settings
try:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
