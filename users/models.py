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
    can_review_talks = models.BooleanField(
        default=False,
        help_text="Grants permission to review talk proposals",
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password"]
