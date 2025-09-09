"""users models."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import TimeStampedModel
from users.choices import UserRoleChoices
from users.managers import UserManager


class User(AbstractUser):
    """User model."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    username = models.CharField(
        _("username"), max_length=150, unique=True, db_index=True
    )
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    role = models.ForeignKey(
        "UserRole",
        on_delete=models.CASCADE,
        related_name="users_role",
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def get_full_name(self):
        """Return the full name of the user."""
        return self.username

    def get_role(self):
        """Get user role."""
        return self.role

    def check_user_role(self, role: str) -> bool:
        """Check user role."""
        return self.role.role == role

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role.role == UserRoleChoices.ADMIN.value

    def is_organizer(self) -> bool:
        """Check if user is an organizer."""
        return self.role.role == UserRoleChoices.ORGANIZER.value

    def is_attendance(self) -> bool:
        """Check if user is an attendance."""
        return self.role.role == UserRoleChoices.ATTENDEE.value

    def is_speaker(self) -> bool:
        """Check if user is a speaker."""
        return self.role.role == UserRoleChoices.SPEAKER.value

    def is_organizer_or_admin(self) -> bool:
        """Check if user is an organizer admin."""
        return self.is_admin() or self.is_organizer()


class UserRole(TimeStampedModel):
    """User role model."""

    role = models.CharField(max_length=20, choices=UserRoleChoices.choices)
