"""Views for Web3 Badges & Gamification."""

import contextlib
import uuid

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from badges.models import BadgeDefinition, BadgeStatusChoices, SpeakerBadge
from badges.relayer import award_badge_on_chain
from badges.serializers import (
    BadgeDefinitionSerializer,
    ClaimBadgeRequestSerializer,
    SpeakerBadgeSerializer,
)
from badges.services import evaluate_speaker_badges
from profiles.models.speaker_models import SpeakerProfile, get_speaker_profile


class BadgeDefinitionsListView(APIView):
    """List all available Web3 badge definitions."""

    permission_classes = [AllowAny]

    @extend_schema(responses=BadgeDefinitionSerializer(many=True))
    def get(self, request):
        """Retrieve all badge definitions ordered by token ID."""
        badges = BadgeDefinition.objects.all().order_by("token_id")
        serializer = BadgeDefinitionSerializer(badges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerBadgesListView(APIView):
    """Retrieve all badges for a specific speaker profile by slug or ID."""

    permission_classes = [AllowAny]

    @extend_schema(responses=SpeakerBadgeSerializer(many=True))
    def get(self, request, slug):
        """Retrieve speaker badge eligibility and on-chain status."""
        # Allow lookup by slug, UUID, or username
        speaker = SpeakerProfile.objects.filter(slug=slug).first()
        if not speaker:
            with contextlib.suppress(ValueError, AttributeError):
                speaker = SpeakerProfile.objects.filter(pk=uuid.UUID(str(slug))).first()
        if not speaker:
            speaker = get_object_or_404(SpeakerProfile, user_account__username=slug)

        # Fresh evaluation based on current metrics
        evaluate_speaker_badges(speaker)

        badges = (
            SpeakerBadge.objects.filter(speaker=speaker)
            .select_related("badge")
            .order_by("badge__token_id")
        )
        serializer = SpeakerBadgeSerializer(badges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClaimBadgeView(APIView):
    """Record an on-chain mint claim for an eligible badge with gasless relayer support."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=ClaimBadgeRequestSerializer,
        responses=SpeakerBadgeSerializer,
    )
    def post(self, request):
        """Claim an eligible badge and mint it on-chain via relayer."""
        speaker = None
        if request.user and request.user.is_authenticated:
            speaker = get_speaker_profile(request.user)

        serializer = ClaimBadgeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Fallback to speaker_slug if speaker not found via auth session
        speaker_slug = data.get("speaker_slug", "").strip()
        if not speaker and speaker_slug:
            speaker = SpeakerProfile.objects.filter(slug=speaker_slug).first()
            if not speaker:
                with contextlib.suppress(ValueError, AttributeError):
                    speaker = SpeakerProfile.objects.filter(
                        pk=uuid.UUID(str(speaker_slug))
                    ).first()
            if not speaker:
                speaker = SpeakerProfile.objects.filter(
                    user_account__username=speaker_slug
                ).first()

        if not speaker:
            # Fallback to the first available speaker profile if in dev
            speaker = SpeakerProfile.objects.first()

        if not speaker:
            return Response(
                {"detail": "Speaker profile could not be found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_id = data["token_id"]
        recipient_address = data["recipient_address"]
        client_tx_hash = data.get("tx_hash", "").strip()

        badge_def = get_object_or_404(BadgeDefinition, token_id=token_id)

        # Ensure latest eligibility status
        evaluate_speaker_badges(speaker)

        speaker_badge = get_object_or_404(
            SpeakerBadge,
            speaker=speaker,
            badge=badge_def,
        )

        if speaker_badge.status == BadgeStatusChoices.LOCKED:
            return Response(
                {
                    "detail": f"You have not unlocked the {badge_def.name} badge yet. Criteria: {badge_def.criteria}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Execute on-chain minting via Gasless Relayer if client hasn't provided a tx_hash
        final_tx_hash = client_tx_hash
        if not final_tx_hash:
            relayer_res = award_badge_on_chain(recipient_address, token_id)
            final_tx_hash = relayer_res.get("tx_hash", "")

        # Update to claimed
        speaker_badge.status = BadgeStatusChoices.CLAIMED
        speaker_badge.recipient_address = recipient_address
        speaker_badge.tx_hash = final_tx_hash
        speaker_badge.claimed_at = timezone.now()
        speaker_badge.save(
            update_fields=[
                "status",
                "recipient_address",
                "tx_hash",
                "claimed_at",
                "updated_at",
            ]
        )

        return Response(
            SpeakerBadgeSerializer(speaker_badge).data,
            status=status.HTTP_200_OK,
        )


class BadgeMetadataView(APIView):
    """ERC-1155 compliant metadata endpoint for Base/OpenSea."""

    permission_classes = [AllowAny]

    def get(self, request, token_id):
        """Return ERC-1155 token metadata JSON."""
        # Support token_id formatted as int or hex (e.g. {id}.json)
        raw_id = str(token_id).replace(".json", "")
        try:
            tid = int(raw_id, 16) if raw_id.startswith("0x") else int(raw_id)
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid token ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        badge = get_object_or_404(BadgeDefinition, token_id=tid)

        metadata = {
            "name": f"SpeakWise: {badge.name}",
            "description": badge.description,
            "image": f"https://speakwise.live/badges/{badge.slug}.png",
            "external_url": "https://speakwise.live/badges",
            "attributes": [
                {"trait_type": "Tier", "value": badge.tier.title()},
                {"trait_type": "Requirement", "value": badge.criteria},
                {"trait_type": "Network", "value": "Base L2"},
                {"trait_type": "Soulbound", "value": "Yes (Non-Transferable)"},
            ],
        }
        return Response(metadata, status=status.HTTP_200_OK)
