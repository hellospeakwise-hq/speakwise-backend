"""Tests for the feedback app."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from feedbacks.models import Feedback


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
