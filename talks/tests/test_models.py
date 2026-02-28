"""Talks tests."""

from django.test import TestCase

from events.models import Country, Event, Location
from speakers.models import SpeakerProfile
from talks.models import TalkReviewComment, Talks
from talks.serializers import TalkSerializer
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
            description="This is a sample talk description.",
            speaker=self.speaker_profile,
            duration=60,
            category="frontend",
            event=Event.objects.create(
                title="Sample Event",
                description="This is a sample event.",
                location=Location.objects.create(
                    venue="Sample Venue",
                    address="123 Sample St",
                    city="Sample City",
                    state="Sample State",
                    country=Country.objects.create(name="Sample Country"),
                ),
            ),
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
                "event",
                "speaker_name",
                "slug",
                "is_public",
                "is_reviewable",
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


class TestTalkReviewComment(TestCase):
    """test talk review comment model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser2",
            first_name="Test",
            last_name="User2",
            email="testuser2@mail.com",
            password="testpass2",
        )

        self.speaker_profile = SpeakerProfile.objects.create(user_account=self.user)
        self.talk = Talks.objects.create(
            title="Sample Talk 2",
            description="This is another sample talk description.",
            speaker=self.speaker_profile,
            duration=45,
            category="backend",
            event=Event.objects.create(
                title="Sample Event 2",
                description="This is another sample event.",
                location=Location.objects.create(
                    venue="Sample Venue 2",
                    address="456 Sample St",
                    city="Sample City 2",
                    state="Sample State 2",
                    country=Country.objects.create(name="Sample Country 2"),
                ),
            ),
        )
        self.comment = "This is a review comment for the talk."
        self.talk_review_comment = TalkReviewComment.objects.create(
            comment=self.comment, talk=self.talk, rating=5
        )

    def test_talk_review_comment_create(self):
        """Test that a talk review comment is created correctly."""
        assert self.talk_review_comment.comment == self.comment
        assert self.talk_review_comment.talk == self.talk
        assert self.talk_review_comment.id is not None

    def test_talk_review_comment_str(self):
        """Test the string representation of the talk review comment."""
        expected_str = f"{self.talk.title} - {self.comment[:50]}..."
        assert str(self.talk_review_comment) == expected_str

    def test_talk_review_comment_update(self):
        """Test updating a talk review comment."""
        new_comment = "This is an updated review comment."
        self.talk_review_comment.comment = new_comment
        self.talk_review_comment.save()
        assert self.talk_review_comment.comment == new_comment

    def test_talk_review_comment_delete(self):
        """Test deleting a talk review comment."""
        comment_id = self.talk_review_comment.id
        self.talk_review_comment.delete()
        assert not self.talk.talk_sessions.filter(id=comment_id).exists()
