"""Test-only settings — uses in-memory SQLite so tests run without Postgres.

For Postgres-backed tests (e.g. CI), set DB_NAME via environment variable and
run with ``--settings=speakwise.settings.local`` instead.
"""

from speakwise.settings.base import *  # noqa: F401, F403

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

MIGRATION_MODULES = {
    app: None
    for app in [
        "attendees",
        "cfps",
        "events",
        "eventschedules",
        "eventsessions",
        "feedbacks",
        "organizations",
        "speakerrequests",
        "speakers",
        "talks",
        "teams",
        "users",
    ]
}
