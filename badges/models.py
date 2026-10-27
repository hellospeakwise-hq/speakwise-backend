"""Models for Web3 Soulbound Badges and Gamification."""

import uuid

from django.db import models

from badges.choices import (
    BadgeMetricTypeChoices,
    BadgeStatusChoices,
    BadgeTierChoices,
)
from base.models import TimeStampedModel
from profiles.models.speaker_models import SpeakerProfile


class BadgeDefinition(TimeStampedModel):
    """Definition for an on-chain achievement badge (ERC-1155 token ID)."""

    token_id = models.PositiveIntegerField(
        primary_key=True,
        help_text="ERC-1155 token ID on Base (1: Genesis Speaker, 2: In Demand, etc.)",
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    tier = models.CharField(
        max_length=20,
        choices=BadgeTierChoices.choices,
        default=BadgeTierChoices.BRONZE,
    )
    icon = models.CharField(max_length=50, default="Award")
    emoji = models.CharField(max_length=10, default="🏅")
    criteria = models.CharField(max_length=255, help_text="Human-readable requirement")

    # Evaluation metric fields
    metric_type = models.CharField(
        max_length=50,
        choices=BadgeMetricTypeChoices.choices,
        default=BadgeMetricTypeChoices.TALKS_COUNT,
    )
    metric_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="Numerical threshold needed to unlock this badge",
    )

    class Meta:
        """Meta options for BadgeDefinition."""

        ordering = ["token_id"]
        verbose_name = "Badge Definition"
        verbose_name_plural = "Badge Definitions"

    def __str__(self):
        """Return string representation of badge definition."""
        return f"[{self.token_id}] {self.name} ({self.tier.title()})"


class SpeakerBadge(TimeStampedModel):
    """Tracks a speaker's eligibility and on-chain minting status for a badge."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge = models.ForeignKey(
        BadgeDefinition,
        on_delete=models.CASCADE,
        related_name="awarded_speakers",
    )
    status = models.CharField(
        max_length=20,
        choices=BadgeStatusChoices.choices,
        default=BadgeStatusChoices.LOCKED,
    )

    # On-chain minting fields
    tx_hash = models.CharField(
        max_length=66,
        blank=True,
        null=True,
        help_text="Base transaction hash (0x...)",
    )
    recipient_address = models.CharField(
        max_length=42,
        blank=True,
        null=True,
        help_text="Recipient EVM wallet address (0x...)",
    )
    network = models.CharField(
        max_length=50,
        default="base-sepolia",
        help_text="Blockchain network where badge was minted",
    )
    unlocked_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the speaker met the criteria",
    )
    claimed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the on-chain mint transaction succeeded",
    )

    class Meta:
        """Meta options for SpeakerBadge."""

        unique_together = ("speaker", "badge")
        ordering = ["badge__token_id"]
        verbose_name = "Speaker Badge"
        verbose_name_plural = "Speaker Badges"

    def __str__(self):
        """Return string representation of speaker badge."""
        return (
            f"{self.speaker.user_account.username} - {self.badge.name} ({self.status})"
        )
