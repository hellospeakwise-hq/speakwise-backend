"""Choices for the organizations roles."""

from django.db import models


class OrganizationRole(models.TextChoices):
    """Choices for organization roles."""

    ADMIN = "ADMIN", "Admin"
    MEMBER = "MEMBER", "Member"
