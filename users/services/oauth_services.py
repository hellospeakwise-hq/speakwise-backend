"""OAuth user resolution and one-time code exchange services.

Providers hand back provider-specific identifiers and profile data; this module
normalises them into a ``User`` and issues short-lived, single-use exchange
codes that the frontend trades for real tokens, so credentials never appear in
redirect URLs.
"""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from users.models import OAuthExchangeCode, User


def _hash_code(code: str) -> str:
    """Return a deterministic SHA-256 hash of a high-entropy plaintext code."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _unique_username(base_username) -> str:
    """Return a unique, valid username derived from a provider's display name.

    Sluggifies the provider value (which may contain spaces, accents, or
    characters Django's username validator rejects), falls back to ``user``,
    and appends a numeric suffix until the username is unused.
    """
    normalized = (slugify(base_username or "")[:120] or "user").strip("_-")
    username = normalized
    suffix = 2
    while User.objects.filter(username=username).exists():
        username = f"{normalized}{suffix}"
        suffix += 1
    return username


def get_or_create_oauth_user(*, email, username) -> tuple[User, bool]:
    """Resolve an OAuth identity to a verified user.

    Existing users are looked up by email and marked verified when the provider
    proves the email again. New users are created already verified, with a
    collision-safe, provider-derived username.

    Returns:
        ``(user, created)`` where ``created`` is True for a new account.
    """
    user = User.objects.filter(email=email).first()
    if user is not None:
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
        return user, False

    if not email:
        raise ValidationError({"detail": "Email not found from provider."})

    return (
        User.objects.create(
            email=email,
            username=_unique_username(username),
            is_email_verified=True,
        ),
        True,
    )


def create_exchange_code(user) -> str:
    """Issue a new one-time exchange code for ``user`` and return the plaintext.

    The plaintext is a high-entropy random token; only its hash is stored. The
    token is handed to the frontend in a redirect URL and exchanged for auth
    tokens via :func:`consume_exchange_code`.
    """
    code = secrets.token_urlsafe(32)
    OAuthExchangeCode.objects.create(
        user=user,
        code_hash=_hash_code(code),
        expires_at=timezone.now()
        + timedelta(seconds=settings.OAUTH_EXCHANGE_CODE_EXPIRY_SECONDS),
    )
    return code


def consume_exchange_code(code: str) -> User:
    """Validate and consume a one-time exchange code, returning its user.

    Raises ``ValidationError`` for unknown, already-used, or expired codes. A
    consumed code can never be used twice.
    """
    exchange = OAuthExchangeCode.objects.filter(code_hash=_hash_code(code)).first()
    if exchange is None or exchange.is_used or exchange.is_expired:
        raise ValidationError({"detail": "Invalid or expired authentication code."})

    exchange.is_used = True
    exchange.save(update_fields=["is_used"])
    return exchange.user
