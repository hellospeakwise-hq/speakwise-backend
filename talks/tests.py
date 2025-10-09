"""Talks tests."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Country, Event, Location
from organizers.models import OrganizerProfile
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
            first_name="Test",
            last_name="User",
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


class TestTalkReviewEndpoint(APITestCase):
    """Test TalkReviewRetrieveView endpoint permissions."""

    def setUp(self):
        """Set up test data."""
        # Create roles
        self.talk_reviewer_role = UserRole.objects.create(
            role=UserRoleChoices.TALK_REVIEWER.value
        )
        self.organizer_role = UserRole.objects.create(
            role=UserRoleChoices.ORGANIZER.value
        )
        self.admin_role = UserRole.objects.create(role=UserRoleChoices.ADMIN.value)
        self.speaker_role = UserRole.objects.create(role=UserRoleChoices.SPEAKER.value)
        self.attendee_role = UserRole.objects.create(
            role=UserRoleChoices.ATTENDEE.value
        )

        # Create users
        self.talk_reviewer_user = User.objects.create(
            username="reviewer",
            email="reviewer@test.com",
            password="testpass123",
            role=self.talk_reviewer_role,
        )
        self.organizer_user = User.objects.create(
            username="organizer",
            email="organizer@test.com",
            password="testpass123",
            role=self.organizer_role,
        )
        self.admin_user = User.objects.create(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            role=self.admin_role,
        )
        self.speaker_user = User.objects.create(
            username="speaker",
            email="speaker@test.com",
            password="testpass123",
            role=self.speaker_role,
        )
        self.attendee_user = User.objects.create(
            username="attendee",
            email="attendee@test.com",
            password="testpass123",
            role=self.attendee_role,
        )
        self.other_speaker_user = User.objects.create(
            username="other_speaker",
            email="other_speaker@test.com",
            password="testpass123",
            role=self.speaker_role,
        )

        # Create organizer profile
        self.organizer_profile = OrganizerProfile.objects.create(
            user_account=self.organizer_user
        )

        # Create events
        self.event1 = Event.objects.create(
            title="PyCon 2025",
            event_nickname="pycon25",
            organizer=self.organizer_profile,
        )
        self.event2 = Event.objects.create(
            title="DjangoCon 2025",
            event_nickname="djangocon25",
            organizer=self.organizer_profile,
        )

        # Create speaker profiles
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user
        )
        self.other_speaker_profile = SpeakerProfile.objects.create(
            user_account=self.other_speaker_user
        )

        # Create talks
        self.talk_event1 = Talks.objects.create(
            title="Python Best Practices",
            description="Learn Python best practices",
            speaker=self.speaker_profile,
            duration=60,
            category="backend",
            event=self.event1,
        )
        self.talk_event2 = Talks.objects.create(
            title="Django Tips",
            description="Django performance tips",
            speaker=self.other_speaker_profile,
            duration=45,
            category="backend",
            event=self.event2,
        )

        # URL for review endpoint
        self.review_url_event1 = reverse(
            "talks:talk-review", kwargs={"pk": self.talk_event1.pk}
        )
        self.review_url_event2 = reverse(
            "talks:talk-review", kwargs={"pk": self.talk_event2.pk}
        )

    def test_talk_reviewer_can_access_review_endpoint(self):
        """Test that a talk reviewer can access the review endpoint."""
        self.client.force_authenticate(user=self.talk_reviewer_user)
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Python Best Practices"

    def test_organizer_can_access_review_endpoint(self):
        """Test that an organizer can access the review endpoint."""
        self.client.force_authenticate(user=self.organizer_user)
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_review_endpoint(self):
        """Test that an admin can access the review endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_200_OK

    def test_speaker_of_same_event_cannot_review_talks(self):
        """Test that a speaker of the same event cannot review talks."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_speaker_of_different_event_can_review_talks(self):
        """Test that a speaker of a different event can review talks."""
        # other_speaker has talks in event2, trying to review event1 talk
        self.client.force_authenticate(user=self.other_speaker_user)
        response = self.client.get(self.review_url_event1)
        # This should fail because speaker doesn't have reviewer permission
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_access_review_endpoint(self):
        """Test that an unauthenticated user cannot access the review endpoint."""
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_regular_attendee_cannot_access_review_endpoint(self):
        """Test that a regular attendee cannot access the review endpoint."""
        self.client.force_authenticate(user=self.attendee_user)
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_talk_reviewer_with_speaker_role_in_same_event_blocked(self):
        """Test that even a talk reviewer who is a speaker in same event is blocked."""
        # Give speaker user the talk reviewer role
        self.speaker_user.role = self.talk_reviewer_role
        self.speaker_user.save()

        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.get(self.review_url_event1)
        # Should be blocked because they're a speaker in event1
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_review_endpoint_returns_nested_data(self):
        """Test that review endpoint returns nested speaker and event data."""
        self.client.force_authenticate(user=self.talk_reviewer_user)
        response = self.client.get(self.review_url_event1)
        assert response.status_code == status.HTTP_200_OK

        # Check nested data
        assert "speaker" in response.data
        assert "event" in response.data
        assert "user_account" in response.data["speaker"]
        assert response.data["event"]["title"] == "PyCon 2025"
