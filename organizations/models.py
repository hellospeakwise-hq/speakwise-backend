"""Models for managing organizations and their memberships."""

from django.contrib.auth import get_user_model
from django.db import models

from base.models import TimeStampedModel

# Organizations file upload directory
ORGANIZATION_UPLOAD_DIR = "organizations/logos/"


class OrganizationRole(models.TextChoices):
    """Organization role choices."""

    ADMIN = "admin", "Admin"
    ORGANIZER = "organizer", "Organizer"


class Organization(TimeStampedModel):
    """Organization model for managing multiple organizers."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to=ORGANIZATION_UPLOAD_DIR, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Track who created the organization (becomes the first admin)
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="created_organizations"
    )

    # Many-to-many relationship with users through OrganizationMembership
    members = models.ManyToManyField(
        get_user_model(),
        through="OrganizationMembership",
        through_fields=("organization", "user"),
        related_name="organizations",
    )

    class Meta:
        """Meta options for Organization model."""

        db_table = "organizations"
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        """String representation."""
        return self.name

    def get_admins(self):
        """Get all admin members of the organization."""
        return self.members.filter(
            organization_memberships__role=OrganizationRole.ADMIN,
            organization_memberships__organization=self,
        )

    def get_organizers(self):
        """Get all organizer members (including admins) of the organization."""
        return self.members.filter(organization_memberships__organization=self)

    def is_admin(self, user):
        """Check if a user is an admin of this organization."""
        return self.organization_memberships.filter(
            user=user, role=OrganizationRole.ADMIN
        ).exists()

    def is_member(self, user):
        """Check if a user is a member of this organization."""
        return self.organization_memberships.filter(user=user).exists()


class OrganizationMembership(TimeStampedModel):
    """Through model for Organization-User relationship with roles."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="organization_memberships"
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=OrganizationRole.choices,
        default=OrganizationRole.ORGANIZER,
    )
    added_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="added_memberships",
    )
    is_active = models.BooleanField(default=True)

    # Permissions for organizer tasks
    can_review_talks = models.BooleanField(default=True)
    can_manage_events = models.BooleanField(default=False)  # Only admins by default
    can_add_organizers = models.BooleanField(default=False)  # Only admins by default

    class Meta:
        """Meta options for OrganizationMembership model."""

        db_table = "organization_memberships"
        unique_together = ("organization", "user")
        verbose_name = "Organization Membership"
        verbose_name_plural = "Organization Memberships"

    def __str__(self):
        """String representation."""
        return f"{self.user.username} - {self.organization.name} ({self.role})"

    def save(self, *args, **kwargs):
        """Override save to set admin permissions."""
        if self.role == OrganizationRole.ADMIN:
            if self.can_manage_events is False:
                self.can_manage_events = True
            if self.can_add_organizers is False:
                self.can_add_organizers = True
        super().save(*args, **kwargs)
