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
    fist_name = models.CharField(max_length=255, help_text="Fist name", null=True)
    last_name = models.CharField(max_length=255, help_text="Last name", null=True)
    username = models.CharField(
        _("username"), max_length=150, unique=True, db_index=True
    )
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    nationality = models.CharField(max_length=255, help_text="Nationality", null=True)
    role = models.ForeignKey(
        "UserRole",
        on_delete=models.CASCADE,
        related_name="users_role",
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password"]

    def __str__(self):
        """String representation."""
        return self.username

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

    def is_organization_admin(self, organization=None):
        """Check if user is an admin of any organization or a specific organization."""
        if organization:
            return self.organization_memberships.filter(
                organization=organization, role="admin", is_active=True
            ).exists()
        return self.organization_memberships.filter(
            role="admin", is_active=True
        ).exists()

    def is_organization_member(self, organization=None):
        """Check if user is a member of any organization or a specific organization."""
        if organization:
            return self.organization_memberships.filter(
                organization=organization, is_active=True
            ).exists()
        return self.organization_memberships.filter(is_active=True).exists()

    def get_organizations_as_admin(self):
        """Get all organizations where user is an admin."""
        return [
            membership.organization
            for membership in self.organization_memberships.filter(
                role="admin", is_active=True
            )
        ]

    def get_organizations_as_member(self):
        """Get all organizations where user is a member."""
        return [
            membership.organization
            for membership in self.organization_memberships.filter(is_active=True)
        ]


class UserRole(TimeStampedModel):
    """User role model."""

    role = models.CharField(max_length=20, choices=UserRoleChoices.choices)

    def __str__(self):
        """String representation."""
        return self.role
