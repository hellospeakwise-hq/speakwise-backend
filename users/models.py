"""users models."""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from base.models import TimeStampedModel
from users.choices import UserRoleChoices
from users.managers import UserManager
import uuid


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


class UserRole(TimeStampedModel):
    """User role model."""

    role = models.CharField(max_length=20, choices=UserRoleChoices.choices)
