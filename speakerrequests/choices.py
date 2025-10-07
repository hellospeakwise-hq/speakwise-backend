"""speaker request choices."""

from django.db import models


class RequestStatusChoices(models.TextChoices):
    """speaker request status choices."""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
