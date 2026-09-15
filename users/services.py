"""OTP issuance, verification, and resend services.

All OTP business rules live here so views and serializers stay thin. Codes are
generated with ``secrets`` and stored only as salted hashes — the plaintext
code never touches the database or logs.

Delivery is currently email-only, isolated behind :func:`send_otp_email`. An
SMS channel can be added later behind the same interface without touching
callers (for example a ``send_otp_sms`` used in place of the email helper).
"""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from users.models import OtpCode, User
from users.tasks import send_otp_email_task


def _generate_otp_code() -> str:
    """Return a cryptographically random numeric OTP code."""
    return f"{secrets.randbelow(10**settings.OTP_CODE_LENGTH):0{settings.OTP_CODE_LENGTH}d}"


def _hash_otp_code(code: str, salt: str) -> str:
    """Hash the OTP code with its per-record salt."""
    return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()


def _get_verifiable_user(email: str) -> User:
    """Look up a user by normalized email without leaking enumeration details."""
    user = User.objects.filter(email=email).first()
    if user is None:
        raise ValidationError({"detail": "Invalid email or OTP code."})
    return user


def issue_otp(user) -> str:
    """Generate and persist a fresh OTP for the user, returning the plaintext.

    Any previously issued, unused OTP for the user is invalidated so at most
    one active code exists. The returned plaintext is only ever used to build
    the delivery message and must never be logged.
    """
    OtpCode.objects.filter(user=user, is_used=False).update(is_used=True)

    code = _generate_otp_code()
    salt = secrets.token_hex(16)
    OtpCode.objects.create(
        user=user,
        code_hash=_hash_otp_code(code, salt),
        salt=salt,
        expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )
    return code


def verify_otp_by_email(email: str, code: str) -> User:
    """Verify ``code`` for the user with ``email`` and mark them verified.

    Raises ``ValidationError`` on unknown email, an already-verified account,
    an unknown/expired/locked OTP, or an incorrect code.
    """
    user = _get_verifiable_user(email)

    if user.is_email_verified:
        raise ValidationError({"detail": "Email is already verified."})

    otp = OtpCode.objects.filter(user=user, is_used=False).first()
    if otp is None:
        raise ValidationError({"detail": "Invalid email or OTP code."})

    if otp.is_expired:
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        raise ValidationError({"detail": "OTP code has expired. Request a new one."})

    if otp.is_locked:
        raise ValidationError({"detail": "Too many attempts. Request a new OTP code."})

    if not secrets.compare_digest(otp.code_hash, _hash_otp_code(code, otp.salt)):
        otp.attempt_count += 1
        otp.save(update_fields=["attempt_count"])
        if otp.is_locked:
            raise ValidationError(
                {"detail": "Too many attempts. Request a new OTP code."}
            )
        raise ValidationError({"detail": "Invalid OTP code."})

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])
    return user


def resend_otp_by_email(email: str) -> tuple[User, str]:
    """Issue a new OTP for ``email``, enforcing the resend cooldown.

    Returns ``(user, plaintext_code)`` so the caller can dispatch delivery.
    """
    user = _get_verifiable_user(email)

    if user.is_email_verified:
        raise ValidationError({"detail": "Email is already verified."})

    latest = OtpCode.objects.filter(user=user).first()
    if latest is not None and not latest.is_expired:
        cooldown = timedelta(minutes=settings.OTP_RESEND_COOLDOWN_MINUTES)
        if timezone.now() < latest.created_at + cooldown:
            raise ValidationError(
                {"detail": "Too soon to request a new code. Please try again later."}
            )

    return user, issue_otp(user)


def send_otp_email(user: User, code: str) -> None:
    """Dispatch the OTP code to the user by email via the background task.

    This is the single delivery chokepoint for OTP codes.
    """
    send_otp_email_task.enqueue(str(user.id), code)
