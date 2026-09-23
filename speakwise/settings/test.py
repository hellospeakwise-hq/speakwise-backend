"""Test-only settings — uses in-memory SQLite so tests run without Postgres."""

from speakwise.settings.local import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Tests use an isolated in-process cache: no `django_cache` table needed,
# no cross-test leakage through Postgres.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Tasks run inline in tests so `.enqueue()` executes synchronously.
TASKS = {"default": {"BACKEND": "django_tasks.backends.immediate.ImmediateBackend"}}
