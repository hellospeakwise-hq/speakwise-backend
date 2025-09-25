"""Tests for the feedback app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from feedbacks.models import Feedback
from speakers.models import SpeakerProfile
from talks.models import Session, Talks
from users.models import UserRole


class TestFeedback(TestCase):
    """Test feedback models."""

    def setUp(self):
        """Set up test data."""
        # Create a user for attendee
        self.user = get_user_model().objects.create_user(
            username="testattendee",
            email="attendee@mail.com",
            password="testpass123",
            role=UserRole.objects.create(role="attendee"),
        )

        # Create attendee profile with minimal setup
        from attendees.models import AttendeeProfile

        self.attendee = AttendeeProfile.objects.create(
            user_account=self.user,
            email="attendee@mail.com",
            first_name="Test",
            last_name="Attendee",
        )

        self.session = Session.objects.create(
            type="workshop",
            talk=Talks.objects.create(
                title="Test Talk",
                description="A talk for testing",
                speaker=SpeakerProfile.objects.create(
                    user_account=self.user,
                ),
                duration=60,
                category="tech",
            ),
            duration=60,
        )

        # Create a feedback instance
        self.feedback = Feedback.objects.create(
            attendee=self.attendee,
            overall_rating=5,
            engagement=4,
            clarity=5,
            content_depth=4,
            speaker_knowledge=5,
            practical_relevance=4,
            comments="Great session, very informative!",
            is_anonymous=False,
            session=self.session,
        )

        # Create an anonymous feedback instance
        self.anonymous_feedback = Feedback.objects.create(
            attendee=self.attendee,
            overall_rating=3,
            engagement=3,
            clarity=3,
            content_depth=3,
            speaker_knowledge=3,
            practical_relevance=3,
            comments="Could be better.",
            is_anonymous=True,
            session=self.session,
        )

    def test_feedback_creation(self):
        """Test feedback creation."""
        self.assertEqual(self.feedback.attendee, self.attendee)
        self.assertEqual(self.feedback.overall_rating, 5)
        self.assertEqual(self.feedback.engagement, 4)
        self.assertEqual(self.feedback.clarity, 5)
        self.assertEqual(self.feedback.content_depth, 4)
        self.assertEqual(self.feedback.speaker_knowledge, 5)
        self.assertEqual(self.feedback.practical_relevance, 4)
        self.assertEqual(self.feedback.comments, "Great session, very informative!")
        self.assertFalse(self.feedback.is_anonymous)

    def test_feedback_str_method(self):
        """Test feedback string representation."""
        # For anonymous feedback
        expected_anonymous = f"Anonymous Feedback #{self.anonymous_feedback.pk}"
        self.assertEqual(str(self.anonymous_feedback), expected_anonymous)

        # For regular feedback
        expected_regular = f"Feedback #{self.feedback.pk} by {self.attendee}"
        self.assertEqual(str(self.feedback), expected_regular)


class TestFeedbackAPI(APITestCase):
    """Test feedback API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="user@example.com",
            password="password123",
            role=UserRole.objects.create(role="attendee"),
        )
        self.client.force_authenticate(user=self.user)

        # Create attendee profile
        from attendees.models import AttendeeProfile

        self.attendee = AttendeeProfile.objects.create(
            user_account=self.user,
            email="user@example.com",
            first_name="API",
            last_name="User",
        )

        self.session = Session.objects.create(
            type="workshop",
            talk=Talks.objects.create(
                title="Test Talk",
                description="A talk for testing",
                speaker=SpeakerProfile.objects.create(
                    user_account=self.user,
                ),
                duration=60,
                category="tech",
            ),
            duration=60,
        )

        self.session2 = Session.objects.create(
            type="workshop",
            talk=Talks.objects.create(
                title="Test Talk 2",
                description="Another talk for testing",
                speaker=SpeakerProfile.objects.create(
                    user_account=self.user,
                ),
                duration=45,
                category="business",
            ),
            duration=45,
        )

        # Create feedback
        self.feedback = Feedback.objects.create(
            attendee=self.attendee,
            overall_rating=4,
            engagement=4,
            clarity=4,
            content_depth=4,
            speaker_knowledge=4,
            practical_relevance=4,
            comments="Test feedback",
            is_anonymous=False,
            session=self.session2,
        )

    def test_list_feedbacks(self):
        """Test listing feedbacks."""
        url = "/api/feedbacks/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if our feedback is in the response
        self.assertGreater(len(response.data), 0)

    def test_create_feedback(self):
        """Test creating feedback."""
        url = "/api/feedbacks/"
        data = {
            "attendee": self.attendee.id,
            "overall_rating": 5,
            "engagement": 5,
            "clarity": 5,
            "content_depth": 5,
            "speaker_knowledge": 5,
            "practical_relevance": 5,
            "comments": "New feedback",
            "is_anonymous": True,
            "session": self.session.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 2)

    def test_retrieve_feedback(self):
        """Test retrieving a feedback."""
        url = f"/api/feedbacks/{self.feedback.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["comments"], "Test feedback")

    def test_update_feedback(self):
        """Test updating feedback."""
        url = f"/api/feedbacks/{self.feedback.id}/"
        data = {
            "attendee": self.attendee.id,
            "overall_rating": 5,
            "engagement": 5,
            "clarity": 5,
            "content_depth": 5,
            "speaker_knowledge": 5,
            "practical_relevance": 5,
            "comments": "Updated feedback",
            "is_anonymous": False,
            "session": self.session.id,
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.comments, "Updated feedback")

    def test_delete_feedback(self):
        """Test deleting feedback."""
        url = f"/api/feedbacks/{self.feedback.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Feedback.objects.count(), 0)
