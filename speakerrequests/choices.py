"""speaker request choices."""

from django.db import models


class RequestStatusChoices(models.TextChoices):
    """speaker request status choices."""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    IS_EXPIRED = "is_expired", "Is Expired"
    CANCELLED = "cancelled", "Cancelled"


class RequestProposedSessionTypeChoices(models.TextChoices):
    """speaker request proposed session type choices."""

    ONLINE = "online", "Online"
    IN_PERSON = "in_person", "In Person"
