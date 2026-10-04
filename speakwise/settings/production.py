"""Production settings for speakwise."""

import dj_database_url
from dotenv import load_dotenv

from .base import *  # noqa: E402,F403,F401
from .base import BASE_DIR  # noqa: E402

load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
# Do not provide an insecure fallback in production.
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable must be set in production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


def _csv_env(name, default=""):
    """Split a comma-separated env var into a cleaned list."""
    raw = os.environ.get(name, default)
    return [v.strip() for v in raw.split(",") if v.strip()]


ALLOWED_HOSTS = _csv_env(
    "ALLOWED_HOSTS",
    "apis.speak-wise.live,speak-wise.live,www.speak-wise.live",
)

CSRF_TRUSTED_ORIGINS = _csv_env(
    "CSRF_TRUSTED_ORIGINS",
    "https://apis.speak-wise.live,https://speak-wise.live,https://www.speak-wise.live",
)

# Database: prefer a single DATABASE_URL (DigitalOcean Managed Postgres,
# Railway Postgres) and fall back to split DB_* vars for Droplet-era envs.
# Both platforms terminate TLS in front of the app; DO Managed Postgres
# additionally requires sslmode=require on the database connection itself.
_DATABASE_URL = os.environ.get("DATABASE_URL")
if _DATABASE_URL:
    # Railway internal Postgres (railway.internal) does not support SSL.
    # External managed Postgres (e.g. DigitalOcean) requires ssl_require=True.
    _ssl_required = "railway.internal" not in _DATABASE_URL
    DATABASES = {
        "default": dj_database_url.parse(
            _DATABASE_URL,
            conn_max_age=600,
            ssl_require=_ssl_required,
        )
    }
else:
    _db_options = {}
    if os.environ.get("DB_SSLMODE", "require").lower() != "disable":
        _db_options = {"sslmode": os.environ.get("DB_SSLMODE", "require")}
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT"),
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": _db_options,
        }
    }

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT") or os.path.join(BASE_DIR, "staticfiles")

# Add CORS settings for your Next.js frontend
_CORS_EXTRA = _csv_env("CORS_ALLOWED_ORIGINS_EXTRA", "")
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://www.speakwise.live",
    "https://speakwise.live",
    "https://www.speak-wise.live",
    "https://speak-wise.live",
    *_CORS_EXTRA,
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://speakwise-.*\.vercel\.app$",
]

CORS_ALLOW_CREDENTIALS = True
# Media files: local disk by default, S3-compatible object storage when
# AWS_* env vars are present (DigitalOcean Spaces now, reused from Railway).
# Ephemeral PaaS filesystems lose local uploads on every redeploy.
MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT") or os.path.join(BASE_DIR, "media")

_AWS_BUCKET = os.environ.get("AWS_STORAGE_BUCKET_NAME")
_AWS_ENDPOINT = os.environ.get("AWS_S3_ENDPOINT_URL")
if _AWS_BUCKET:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": _AWS_BUCKET,
                "endpoint_url": _AWS_ENDPOINT,
                "access_key": os.environ.get("AWS_ACCESS_KEY_ID"),
                "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
                "region_name": os.environ.get("AWS_S3_REGION_NAME", "fra1"),
                "default_acl": "public-read",
                "querystring_auth": False,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# Security settings: both DigitalOcean App Platform and Railway terminate TLS
# at the load balancer and forward X-Forwarded-Proto, so the app must trust
# that header and set Secure cookies + HSTS.
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 year (preload requirement)
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
USE_TZ = True

# Cache and tasks inherit the Postgres-backed defaults from base.py.

# Email settings
ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.environ.get("MAILGUN_SENDER_DOMAIN"),
}

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL")

# Logging: stdout only. File handlers assume a writable persistent disk that
# does not exist on App Platform / Railway ephemeral containers, and the
# non-root runtime user cannot create files outside /app. Both platforms
# capture stdout/stderr automatically.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} {module} {process:d} {thread:d} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
