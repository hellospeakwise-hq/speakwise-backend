"""Choices for Web3 Badges & Gamification."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class BadgeTierChoices(models.TextChoices):
    """Badge tier levels (bronze, silver, gold)."""

    BRONZE = "bronze", _("Bronze")
    SILVER = "silver", _("Silver")
    GOLD = "gold", _("Gold")


class BadgeStatusChoices(models.TextChoices):
    """Badge status lifecycle choices."""

    LOCKED = "locked", _("Locked")
    ELIGIBLE = "eligible", _("Eligible to Mint")
    CLAIMED = "claimed", _("Claimed On-Chain")


class BadgeMetricTypeChoices(models.TextChoices):
    """Metric types used to evaluate badge unlock eligibility."""

    TALKS_COUNT = "talks_count", _("Talks Count")
    REQUESTS_COUNT = "requests_count", _("Speaker Requests Accepted")
    FEEDBACKS_COUNT = "feedbacks_count", _("Feedbacks Received")
    RATING_AVG = "rating_avg", _("Average Feedback Rating")
