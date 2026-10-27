"""Tests for Web3 Badges Gamification engine and API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from badges.choices import BadgeStatusChoices, BadgeTierChoices
from badges.models import BadgeDefinition, SpeakerBadge
from badges.services import evaluate_speaker_badges
from profiles.models.speaker_models import SpeakerExperiences, SpeakerProfile

User = get_user_model()


class BadgesEngineTestCase(TestCase):
    """Test suite for badges evaluation and claiming workflow."""

    def setUp(self):
        """Set up test user, speaker profile, and badge definitions."""
        self.client = APIClient()

        # Create user & speaker
        self.user = User.objects.create_user(
            username="testspeaker",
            email="speaker@test.com",
            password="testpassword123",
            first_name="Jane",
            last_name="Speaker",
        )
        self.speaker = SpeakerProfile.objects.create(
            user_account=self.user,
            slug="testspeaker",
        )

        # Seed badges
        self.badge_genesis = BadgeDefinition.objects.create(
            token_id=1,
            name="Genesis Speaker",
            slug="genesis-speaker",
            tier=BadgeTierChoices.BRONZE,
            criteria="Add 1 speaking experience",
            metric_type="talks_count",
            metric_threshold=1.0,
        )
        self.badge_road_warrior = BadgeDefinition.objects.create(
            token_id=4,
            name="Road Warrior",
            slug="road-warrior",
            tier=BadgeTierChoices.SILVER,
            criteria="Deliver 3 speaking experiences",
            metric_type="talks_count",
            metric_threshold=3.0,
        )

    def test_evaluate_badges_unlocked_on_first_talk(self):
        """Speaker with 0 talks has badges locked; with 1 talk, Genesis Speaker unlocks."""
        evaluate_speaker_badges(self.speaker)
        badge1 = SpeakerBadge.objects.get(
            speaker=self.speaker, badge=self.badge_genesis
        )
        self.assertEqual(badge1.status, BadgeStatusChoices.LOCKED)

        # Add 1 talk experience
        SpeakerExperiences.objects.create(
            speaker=self.speaker,
            topic="Intro to Web3 on Base",
            event_name="BaseCamp Global",
            event_date="2026-05-15",
        )

        evaluate_speaker_badges(self.speaker)
        badge1.refresh_from_db()
        self.assertEqual(badge1.status, BadgeStatusChoices.ELIGIBLE)

        # Road warrior requires 3 talks, so remains locked
        badge4 = SpeakerBadge.objects.get(
            speaker=self.speaker, badge=self.badge_road_warrior
        )
        self.assertEqual(badge4.status, BadgeStatusChoices.LOCKED)

    def test_speaker_badges_api_view(self):
        """GET /api/speakers/<slug>/badges/ returns speaker badges."""
        url = reverse("badges:speaker-badges", kwargs={"slug": self.speaker.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_claim_badge_flow(self):
        """Speaker can claim an eligible badge on-chain with tx_hash."""
        # Make badge eligible
        SpeakerExperiences.objects.create(
            speaker=self.speaker,
            topic="Building on Base",
            event_name="Base L2 Summit",
            event_date="2026-06-01",
        )
        evaluate_speaker_badges(self.speaker)

        self.client.force_authenticate(user=self.user)
        claim_url = reverse("badges:claim-badge")

        payload = {
            "token_id": 1,
            "recipient_address": "0x1234567890123456789012345678901234567890",
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        }
        response = self.client.post(claim_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], BadgeStatusChoices.CLAIMED)
        self.assertEqual(response.data["tx_hash"], payload["tx_hash"])
        self.assertIn("sepolia.basescan.org", response.data["basescan_url"])
