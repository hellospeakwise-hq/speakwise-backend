"""Serializers for Web3 Soulbound Badges."""

from django.conf import settings
from rest_framework import serializers

from badges.models import BadgeDefinition, SpeakerBadge


class BadgeDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for badge definitions."""

    class Meta:
        """Meta options for BadgeDefinitionSerializer."""

        model = BadgeDefinition
        fields = [
            "token_id",
            "name",
            "slug",
            "description",
            "tier",
            "icon",
            "emoji",
            "criteria",
            "metric_type",
            "metric_threshold",
        ]


class SpeakerBadgeSerializer(serializers.ModelSerializer):
    """Serializer for a speaker's awarded badge."""

    badge = BadgeDefinitionSerializer(read_only=True)
    basescan_url = serializers.SerializerMethodField()

    class Meta:
        """Meta options for SpeakerBadgeSerializer."""

        model = SpeakerBadge
        fields = [
            "id",
            "badge",
            "status",
            "tx_hash",
            "recipient_address",
            "network",
            "unlocked_at",
            "claimed_at",
            "basescan_url",
        ]

    def get_basescan_url(self, obj) -> str | None:
        """Return BaseScan block explorer transaction URL."""
        if obj.tx_hash and not str(obj.tx_hash).startswith("sim_"):
            return f"https://sepolia.basescan.org/tx/{obj.tx_hash}"
        contract_addr = getattr(
            settings, "SPEAKWISE_BADGES_CONTRACT_ADDRESS", ""
        ).strip()
        if contract_addr and obj.recipient_address:
            return f"https://sepolia.basescan.org/token/{contract_addr}?a={obj.recipient_address}"
        return None


class ClaimBadgeRequestSerializer(serializers.Serializer):
    """Payload to record an on-chain mint claim."""

    token_id = serializers.IntegerField(
        required=True,
        help_text="ERC-1155 token ID being claimed (e.g., 1 for Genesis Speaker)",
    )
    recipient_address = serializers.CharField(
        required=True,
        max_length=42,
        help_text="Recipient EVM wallet address (0x...)",
    )
    tx_hash = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=66,
        help_text="Optional Base L2 transaction hash if client minted directly; otherwise backend relayer executes gasless mint.",
    )
    speaker_slug = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional speaker slug or ID if unauthenticated session.",
    )
