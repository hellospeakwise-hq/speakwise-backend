"""Talks tests."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from speakers.models import SpeakerProfile
from talks.models import Talks
from talks.serializers import TalkReviewSerializer, TalkSerializer
from users.models import User


class TestTalkSerializer(TestCase):
    """Test TalkSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="testuser@mail.com",
            password="testpass",
        )
        self.speaker_profile = SpeakerProfile.objects.create(user_account=self.user)
        self.talk = Talks.objects.create(
            title="Sample Talk",
            slug="sample-talk",
            description="This is a sample talk description.",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
            event="Sample Event",
        )
        self.serializer = TalkSerializer(instance=self.talk)

    def test_talks_model(self):
        """Test that the Talks model instance is created correctly."""
        assert self.talk.title == "Sample Talk"
        assert self.talk.description == "This is a sample talk description."
        assert self.talk.duration == 60
        assert self.talk.category == "frontend"
        assert self.talk.speaker == self.speaker_profile
        assert self.speaker_profile.user_account == self.user

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields."""
        data = self.serializer.data
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "slug",
                "description",
                "speaker",
                "duration",
                "category",
                "presentation_files",
                "event",
                "speaker_name",
                "is_public",
            },
        )

    def test_field_content(self):
        """Test that the field content is correct."""
        data = self.serializer.data
        assert data["title"] == self.talk.title
        assert data["description"] == self.talk.description
        assert data["duration"] == self.talk.duration
        assert data["category"] == self.talk.category
        assert data["speaker"] == self.talk.speaker.id
        assert data["id"] == self.talk.id
        assert data["slug"] == self.talk.slug

    def test_invalid_category(self):
        """Test that an invalid category raises a validation error."""
        invalid_data = {
            "title": "Invalid Talk",
            "slug": "invalid-talk",
            "description": "This talk has an invalid category.",
            "speaker": self.talk.speaker.id,
            "duration": 45,
            "category": "invalid_category",
        }
        serializer = TalkSerializer(data=invalid_data)

        assert not serializer.is_valid()
        assert "category" in serializer.errors


class TestTalkReviewSerializer(TestCase):
    """Test TalkReviewSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="speaker1",
            first_name="Speaker",
            last_name="One",
            email="speaker1@mail.com",
            password="testpass",
        )
        self.speaker_profile = SpeakerProfile.objects.create(user_account=self.user)
        self.talk_public = Talks.objects.create(
            title="Public Talk",
            slug="public-talk",
            description="This is a public talk.",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
            event="Test Event",
            is_public=True,
        )
        self.talk_private = Talks.objects.create(
            title="Private Talk",
            slug="private-talk",
            description="This is a private talk.",
            speaker=self.speaker_profile,
            duration=45,
            category="backend",
            event="Test Event",
            is_public=False,
        )
        self.serializer = TalkReviewSerializer(instance=self.talk_public)

    def test_contains_expected_fields(self):
        """Test that TalkReviewSerializer contains expected fields."""
        data = self.serializer.data
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "slug",
                "description",
                "duration",
                "category",
                "presentation_files",
                "event",
                "is_public",
                "speaker_name",
                "speaker_email",
                "created_at",
            },
        )

    def test_speaker_name(self):
        """Test that speaker name is correctly formatted."""
        data = self.serializer.data
        self.assertEqual(data["speaker_name"], "Speaker One")

    def test_speaker_email(self):
        """Test that speaker email is included."""
        data = self.serializer.data
        self.assertEqual(data["speaker_email"], "speaker1@mail.com")

    def test_is_public_field(self):
        """Test that is_public field is present."""
        data = self.serializer.data
        self.assertTrue(data["is_public"])


class TestTalkReviewListView(TestCase):
    """Test TalkReviewListView API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.speaker_user = User.objects.create(
            username="speaker",
            first_name="Speaker",
            last_name="User",
            email="speaker@mail.com",
            password="testpass",
        )

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
        )

        self.talk_public = Talks.objects.create(
            title="Public Talk",
            slug="public-talk",
            description="Public talk description",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
            event="Test Event",
            is_public=True,
        )

        self.talk_private = Talks.objects.create(
            title="Private Talk",
            slug="private-talk",
            description="Private talk description",
            speaker=self.speaker_profile,
            duration=45,
            category="backend",
            event="Test Event",
            is_public=False,
        )

        self.other_speaker = User.objects.create(
            username="other_speaker",
            first_name="Other",
            last_name="Speaker",
            email="other@mail.com",
            password="testpass",
        )
        self.other_speaker_profile = SpeakerProfile.objects.create(
            user_account=self.other_speaker,
        )

        self.talk_other = Talks.objects.create(
            title="Other Talk",
            slug="other-talk",
            description="Talk by another speaker",
            speaker=self.other_speaker_profile,
            duration=30,
            category="design",
            event="Other Event",
            is_public=True,
        )

    def test_unauthenticated_can_access(self):
        """Test that unauthenticated users can access the review endpoint."""
        response = self.client.get("/api/talks/review/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_can_access(self):
        """Test that authenticated users can access the review endpoint."""
        user = User.objects.create(
            username="regular",
            email="regular@mail.com",
            password="testpass",
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/talks/review/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_only_public_talks(self):
        """Test that only public talks are returned."""
        response = self.client.get("/api/talks/review/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        titles = [talk["title"] for talk in response.data]
        self.assertIn("Public Talk", titles)
        self.assertIn("Other Talk", titles)
        self.assertNotIn("Private Talk", titles)


class TestTalkReviewDetailView(TestCase):
    """Test TalkReviewDetailView API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.speaker_user = User.objects.create(
            username="speaker",
            first_name="Speaker",
            last_name="User",
            email="speaker@mail.com",
            password="testpass",
        )

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
        )

        self.talk_public = Talks.objects.create(
            title="Public Talk",
            slug="public-talk",
            description="Public talk description",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
            event="Test Event",
            is_public=True,
        )

        self.talk_private = Talks.objects.create(
            title="Private Talk",
            slug="private-talk",
            description="Private talk description",
            speaker=self.speaker_profile,
            duration=45,
            category="backend",
            event="Test Event",
            is_public=False,
        )

    def test_unauthenticated_can_access_public_talk(self):
        """Test that unauthenticated users can access a public talk."""
        response = self.client.get(f"/api/talks/review/{self.talk_public.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Public Talk")

    def test_authenticated_can_access_public_talk(self):
        """Test that authenticated users can access a public talk."""
        user = User.objects.create(
            username="reviewer",
            email="reviewer@mail.com",
            password="testpass",
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(f"/api/talks/review/{self.talk_public.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_access_private_talk(self):
        """Test that private talks are not accessible."""
        response = self.client.get(f"/api/talks/review/{self.talk_private.slug}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestTalkReviewDeleteView(TestCase):
    """Test TalkReviewDeleteView API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.speaker_user = User.objects.create(
            username="speaker",
            first_name="Speaker",
            last_name="User",
            email="speaker@mail.com",
            password="testpass",
        )

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
        )

        self.talk = Talks.objects.create(
            title="Talk to Delete",
            slug="talk-to-delete",
            description="Talk description",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
            event="Test Event",
            is_public=True,
        )

    def test_unauthenticated_cannot_delete(self):
        """Test that unauthenticated users cannot delete a talk."""
        response = self.client.delete(f"/api/talks/review/{self.talk.slug}/delete/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_owner_cannot_delete(self):
        """Test that non-owners cannot delete a talk."""
        other_user = User.objects.create(
            username="other",
            first_name="Other",
            last_name="User",
            email="other@mail.com",
            password="testpass",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(f"/api/talks/review/{self.talk.slug}/delete/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete(self):
        """Test that the speaker (owner) can delete their talk."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.delete(f"/api/talks/review/{self.talk.slug}/delete/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Talks.objects.filter(id=self.talk.id).exists())
