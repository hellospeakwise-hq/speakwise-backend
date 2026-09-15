"""users models."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.managers import UserManager


class User(AbstractUser):
    """User model."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    first_name = models.CharField(max_length=255, help_text="Fist name", null=True)
    last_name = models.CharField(max_length=255, help_text="Last name", null=True)
    username = models.CharField(
        _("username"), max_length=150, unique=True, db_index=True
    )
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    nationality = models.CharField(max_length=255, help_text="Nationality", null=True)
    is_email_verified = models.BooleanField(
        default=False,
        help_text=(
            "Whether the user has verified their email address. Email/password "
            "users verify via OTP; OAuth users are verified by the provider."
        ),
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password"]


class OtpCode(models.Model):
    """A single-use, expiring one-time password issued to a user.

    Only the salted SHA-256 hash of the code is stored — the plaintext code is
    never persisted and is only known to the email task. Each user has at most
    one active (unused, unexpired) OTP at a time; issuing a new one invalidates
    the previous one.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code_hash = models.CharField(max_length=64, editable=False)
    salt = models.CharField(max_length=32, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.PositiveIntegerField(default=0)

    class Meta:
        """Meta options."""

        ordering = ["-created_at"]
        verbose_name = "OTP code"
        verbose_name_plural = "OTP codes"

    def __str__(self):
        """Return a human-readable identifier without exposing the code."""
        return f"OTP for {self.user.email} (used={self.is_used})"

    @property
    def is_expired(self) -> bool:
        """Return True when the code is past its expiry time."""
        from django.utils import timezone

        return self.expires_at <= timezone.now()

    @property
    def is_locked(self) -> bool:
        """Return True when too many failed attempts have been made."""
        from django.conf import settings

        return self.attempt_count >= settings.OTP_MAX_ATTEMPTS
