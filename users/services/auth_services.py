"""Credential authentication and failed-login lockout services.

Business rules for the email/password login flow live here so views and
serializers stay thin. The failed-login counter is stored in the Django cache;
it is per-worker until a shared cache backend (e.g. Redis) is configured.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.services.otp_services import issue_otp, send_otp_email

LOGIN_LOCKOUT_MAX_ATTEMPTS = 3
LOGIN_LOCKOUT_WINDOW_SECONDS = 300


def _login_lock_key(email: str) -> str:
    """Return the cache key tracking failed logins for ``email``."""
    return f"login_failures:{email.lower()}"


def is_login_locked(email: str) -> bool:
    """Return True when the email has exceeded the failed-login limit."""
    return cache.get(_login_lock_key(email), 0) >= LOGIN_LOCKOUT_MAX_ATTEMPTS


def record_failed_login(email: str) -> None:
    """Increment the failed-login counter for ``email`` with an expiry window."""
    key = _login_lock_key(email)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=LOGIN_LOCKOUT_WINDOW_SECONDS)


def clear_failed_logins(email: str) -> None:
    """Reset the failed-login counter for a successful login."""
    cache.delete(_login_lock_key(email))


def authenticate_user(email: str, password: str, request=None) -> AbstractBaseUser:
    """Authenticate ``email``/``password``, applying the failed-login lockout.

    Raises ``ValidationError`` with a generic message both for invalid
    credentials and for a locked account, so callers cannot distinguish
    registered emails from unknown ones.

    Args:
        email: The user's email address (the login identifier).
        password: The plaintext password to check.
        request: The optional request used for backend context.

    Returns:
        The authenticated, active user.
    """
    if is_login_locked(email):
        raise ValidationError({"detail": "Unable to log in with provided credentials."})

    user = authenticate(request=request, username=email, password=password)
    if user is None:
        record_failed_login(email)
        raise ValidationError({"detail": "Unable to log in with provided credentials."})

    clear_failed_logins(email)
    return user


def build_auth_payload(user: User) -> dict:
    """Return the JWT access/refresh tokens and serialized user data.

    The user's serialized fields are embedded as token claims (preserving the
    historical behaviour) and also returned in the response body alongside the
    tokens. Profile data is intentionally not part of this payload; login-like
    endpoints append it themselves.
    """
    from users.serializers import UserSerializer

    refresh = RefreshToken.for_user(user)
    for key, value in UserSerializer(user).data.items():
        refresh[key] = value

    data = UserSerializer(user).data
    data["refresh"] = str(refresh)
    data["access"] = str(refresh.access_token)
    return data


def reset_email_verification(user: User) -> None:
    """Mark ``user`` unverified and issue a fresh verification OTP.

    Called when the user's email changes on profile update, so the new address
    must be re-verified before account-protected actions resume.
    """
    user.is_email_verified = False
    user.save(update_fields=["is_email_verified"])
    send_otp_email(user, issue_otp(user))
