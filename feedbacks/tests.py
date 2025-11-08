"""Tests for the feedback app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from feedbacks.models import Feedback
from speakers.models import SpeakerProfile


class TestFeedback(TestCase):
    """Test feedback models."""

    def setUp(self):
        """Set up test data."""
        # Create a user for attendee
        self.user = get_user_model().objects.create(
            username="testattendee",
            email="attendee@mail.com",
            password="testpass123",
        )

        # Create attendee profile with minimal setup
        from attendees.models import AttendeeProfile

        self.attendee = AttendeeProfile.objects.create(user_account=self.user)

        # Create a feedback instance
        self.feedback = Feedback.objects.create(
            overall_rating=5,
            engagement=4,
            clarity=5,
            content_depth=4,
            speaker_knowledge=5,
            practical_relevance=4,
            comments="Great session, very informative!",
            is_anonymous=False,
            is_attendee=True,
        )

    def test_feedback_creation(self):
        """Test feedback creation."""
        self.assertEqual(self.feedback.is_attendee, True)
        self.assertEqual(self.feedback.overall_rating, 5)
        self.assertEqual(self.feedback.engagement, 4)
        self.assertEqual(self.feedback.clarity, 5)
        self.assertEqual(self.feedback.content_depth, 4)
        self.assertEqual(self.feedback.speaker_knowledge, 5)
        self.assertEqual(self.feedback.practical_relevance, 4)
        self.assertEqual(self.feedback.comments, "Great session, very informative!")
        self.assertFalse(self.feedback.is_anonymous)


class FeedbackAPITestCase(APITestCase):
    """Test feedback API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create a user for speaker
        self.speaker_user = get_user_model().objects.create(
            username="testspeaker",
            email="speaker@mail.com",
            password="testpass123",
        )
        self.speak_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user
        )
        self.feedback_url = "/api/feedbacks/"
        self.feedback_data = {
            "overall_rating": 4,
            "engagement": 3,
            "clarity": 4,
            "content_depth": 3,
            "speaker_knowledge": 4,
            "practical_relevance": 3,
            "comments": "Great session, very informative!",
        }

    def test_create_feedback(self):
        """Test feedback creation."""
        response = self.client.post(
            self.feedback_url, self.feedback_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(
            Feedback.objects.get().comments, "Great session, very informative!"
        )

    def test_list_feedback_unauthenticated(self):
        """Test listing feedbacks without authentication."""
        response = self.client.get(self.feedback_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
