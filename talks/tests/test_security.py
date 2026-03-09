"""Security tests for the talks app."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from speakers.models import SpeakerProfile
from talks.models import Talks

User = get_user_model()


class TalkIDORTests(APITestCase):
    """Test suite to ensure IDOR vulnerabilities for talks are patched."""

    def setUp(self):
        """Set up test users and talk dependencies."""
        self.user_a = User.objects.create(email="user_a@test.com", username="user_a")
        self.user_a.set_password("password123")
        self.user_a.save()

        self.user_b = User.objects.create(email="user_b@test.com", username="user_b")
        self.user_b.set_password("password123")
        self.user_b.save()

        self.speaker_a = SpeakerProfile.objects.create(user_account=self.user_a)
        self.speaker_b = SpeakerProfile.objects.create(user_account=self.user_b)

        self.talk_a = Talks.objects.create(
            title="User A Talk",
            description="User A's awesome talk.",
            speaker=self.speaker_a,
            duration=30,
            category="lecture",
        )

    def test_user_b_cannot_delete_user_a_talk(self):
        """Ensure a user cannot delete another speaker's talk (IDOR protection)."""
        # Authenticate as User B
        self.client.force_authenticate(user=self.user_b)

        # User B tries to delete User A's talk
        url = reverse("talks:talk-detail", kwargs={"pk": self.talk_a.pk})
        response = self.client.delete(url)

        # If IDOR is fixed, this returns 404 because get_queryset won't find the object
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "IDOR FIX CONFIRMED: User B cannot find User A's talk.",
        )
