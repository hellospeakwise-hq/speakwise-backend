"""Talks tests."""

from django.test import TestCase

from speakers.models import SpeakerProfile
from talks.models import Talks
from talks.serializers import TalkSerializer
from users.choices import UserRoleChoices
from users.models import User, UserRole


class TestTalkSerializer(TestCase):
    """Test TalkSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser",
            email="testuser@mail.com",
            password="testpass",
            role=UserRole.objects.create(role=UserRoleChoices.SPEAKER.value),
        )
        self.speaker_profile = SpeakerProfile.objects.create(user_account=self.user)
        self.talk = Talks.objects.create(
            title="Sample Talk",
            description="This is a sample talk description.",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
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
                "description",
                "speaker",
                "duration",
                "category",
                "presentation_files",
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

    def test_invalid_category(self):
        """Test that an invalid category raises a validation error."""
        invalid_data = {
            "title": "Invalid Talk",
            "description": "This talk has an invalid category.",
            "speaker": self.talk.speaker.id,
            "duration": 45,
            "category": "invalid_category",
        }
        serializer = TalkSerializer(data=invalid_data)

        assert not serializer.is_valid()
        assert "category" in serializer.errors
