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

# Silence migration output
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None
