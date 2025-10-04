"""speaker request choices."""

from django.db import models


class RequestStatusChoices(models.TextChoices):
    """speaker request status choices."""

    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
