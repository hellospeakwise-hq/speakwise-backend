"""Organizations app models."""

from django.db import models

from base.models import TimeStampedModel
from organizations.choices import OrganizationRole
from users.models import User

# Create your models here.

ORGANIZATION_UPLOAD_DIR = "organizations/logos/"


class Organization(TimeStampedModel):
    """Model representing an organization."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to=ORGANIZATION_UPLOAD_DIR, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, related_name="created_organizations"
    )

    class Meta:
        """Meta class for Organization model."""

        unique_together = ("name", "email")
        ordering = ["name"]

    def __str__(self):
        """String representation of the organization."""
        return self.name


class OrganizationMembership(TimeStampedModel):
    """Model representing membership of a user in an organization."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="organization_memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_memberships"
    )
    role = models.CharField(
        max_length=20, choices=OrganizationRole.choices, default=OrganizationRole.MEMBER
    )
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="added_memberships"
    )

    class Meta:
        """Meta class for OrganizationMembership model."""

        unique_together = ("organization", "user")
        ordering = ["-created_at"]

    def is_admin(self):
        """Check if the user is an admin of the organization."""
        if self.is_active:
            return self.role == OrganizationRole.ADMIN.value
        return False

    def is_organizer(self):
        """Check if the user is an organizer of the organization."""
        if self.is_active:
            return self.role == OrganizationRole.ORGANIZER.value
        return False

    def is_member(self):
        """Check if a user is a member of the organization."""
        if self.is_active:
            return self.role == OrganizationRole.MEMBER.value

    def __str__(self):
        """String representation of the membership."""
        return f"{self.user.username} - {self.organization.name} ({self.role})"
