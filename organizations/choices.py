"""Choices for the organizations roles."""

from django.db import models


class OrganizationRole(models.TextChoices):
    """Choices for organization roles."""

    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    ORGANIZER = "organizer", "Organizer"
