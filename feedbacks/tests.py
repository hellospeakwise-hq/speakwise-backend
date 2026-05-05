"""Tests for the feedback app."""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from attendees.models import AttendeeProfile
from events.models import Event
from feedbacks.models import Feedback, SpeakerFeedbackSettings
from speakers.models import SpeakerProfile
from speakerrequests.models import SpeakerRequest
from organizations.models import Organization, OrganizationMembership

User = get_user_model()


def make_user(username, email):
    # UserManager.create auto-creates a SpeakerProfile
    return User.objects.create(username=username, email=email, password="pass1234")


def make_speaker(user):
    # Return the auto-created SpeakerProfile, not a new one
    return SpeakerProfile.objects.get(user_account=user)


def make_event(title="Test Event"):
    return Event.objects.create(title=title, event_nickname=title.lower())


class TestFeedback(TestCase):
    """Test feedback models."""

    def setUp(self):
        self.user = User.objects.create(
            username="testattendee", email="attendee@mail.com", password="testpass123"
        )
        self.attendee = AttendeeProfile.objects.create(user_account=self.user)
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
        self.assertEqual(self.feedback.is_attendee, True)
        self.assertEqual(self.feedback.overall_rating, 5)
        self.assertEqual(self.feedback.engagement, 4)
        self.assertEqual(self.feedback.clarity, 5)
        self.assertEqual(self.feedback.content_depth, 4)
        self.assertEqual(self.feedback.speaker_knowledge, 5)
        self.assertEqual(self.feedback.practical_relevance, 4)
        self.assertEqual(self.feedback.comments, "Great session, very informative!")
        self.assertFalse(self.feedback.is_anonymous)


class TestSpeakerFeedbackSettings(TestCase):
    """Test SpeakerFeedbackSettings model."""

    def setUp(self):
        self.user = make_user("speaker1", "speaker1@mail.com")
        self.speaker = make_speaker(self.user)
        self.event = make_event("PyCon Ghana")

    def test_default_feedback_enabled(self):
        settings = SpeakerFeedbackSettings.objects.create(
            speaker=self.speaker, event=self.event
        )
        self.assertTrue(settings.feedback_enabled)

    def test_unique_together_constraint(self):
        SpeakerFeedbackSettings.objects.create(speaker=self.speaker, event=self.event)
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            SpeakerFeedbackSettings.objects.create(
                speaker=self.speaker, event=self.event
            )

    def test_str_representation(self):
        settings = SpeakerFeedbackSettings.objects.create(
            speaker=self.speaker, event=self.event
        )
        self.assertIn("enabled", str(settings))
        settings.feedback_enabled = False
        settings.save()
        self.assertIn("disabled", str(settings))


class TestSpeakerFeedbackToggleView(APITestCase):
    """Test POST /api/feedbacks/toggle/."""

    def setUp(self):
        self.client = APIClient()
        self.speaker_user = make_user("speakerabc", "speakerabc@mail.com")
        self.speaker = make_speaker(self.speaker_user)
        self.event = make_event("DjangoCon Africa")

        # Give the speaker an accepted request for this event
        self.org = Organization.objects.create(name="TestOrg", email="testorg@test.com")
        OrganizationMembership.objects.create(
            organization=self.org, user=self.speaker_user, role="ORGANIZER"
        )
        SpeakerRequest.objects.create(
            organizer=self.org,
            speaker=self.speaker,
            event=self.event,
            status="accepted",
            message="Please speak at our event.",
        )

    def _toggle_url(self):
        return reverse("feedbacks:feedback_toggle")

    def test_unauthenticated_returns_401(self):
        resp = self.client.post(self._toggle_url(), {"event": str(self.event.id)})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_accepted_speaker_returns_403(self):
        # UserManager.create auto-creates a SpeakerProfile, but with no accepted request
        other = make_user("notspeaker", "notspeaker@mail.com")
        self.client.force_authenticate(user=other)
        resp = self.client.post(self._toggle_url(), {"event": str(self.event.id)})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_event_returns_400(self):
        self.client.force_authenticate(user=self.speaker_user)
        resp = self.client.post(self._toggle_url(), {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_speaker_not_accepted_for_event_returns_403(self):
        other_event = make_event("PyData Africa")
        self.client.force_authenticate(user=self.speaker_user)
        resp = self.client.post(self._toggle_url(), {"event": str(other_event.id)})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_first_toggle_disables_feedback(self):
        """Default is enabled; first toggle should disable."""
        self.client.force_authenticate(user=self.speaker_user)
        resp = self.client.post(self._toggle_url(), {"event": str(self.event.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["feedback_enabled"])
        settings = SpeakerFeedbackSettings.objects.get(
            speaker=self.speaker, event=self.event
        )
        self.assertFalse(settings.feedback_enabled)

    def test_second_toggle_re_enables_feedback(self):
        self.client.force_authenticate(user=self.speaker_user)
        self.client.post(self._toggle_url(), {"event": str(self.event.id)})
        resp = self.client.post(self._toggle_url(), {"event": str(self.event.id)})
        self.assertTrue(resp.data["feedback_enabled"])

    def test_existing_disabled_setting_toggles_on(self):
        SpeakerFeedbackSettings.objects.create(
            speaker=self.speaker, event=self.event, feedback_enabled=False
        )
        self.client.force_authenticate(user=self.speaker_user)
        resp = self.client.post(self._toggle_url(), {"event": str(self.event.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["feedback_enabled"])


class TestFeedbackCreationToggleGating(APITestCase):
    """Test that feedback submission respects the speaker's feedback toggle."""

    def setUp(self):
        self.client = APIClient()
        self.speaker_user = make_user("gatedspeaker", "gatedspeaker@mail.com")
        self.speaker = make_speaker(self.speaker_user)
        self.event = make_event("AfricasTalking Summit")

        # Seed a verified attendee session via direct session manipulation
        session = self.client.session
        session["attendee_verified"] = True
        session["attendee_email"] = "attendee@test.com"
        session.save()

    def _url(self):
        return reverse("feedbacks:feedbacks_list_create")

    def _payload(self):
        return {
            "speaker": str(self.speaker.id),
            "event": str(self.event.id),
            "overall_rating": 8,
            "engagement": 7,
            "clarity": 8,
            "content_depth": 7,
            "speaker_knowledge": 9,
            "practical_relevance": 7,
            "is_anonymous": False,
            "is_attendee": True,
        }

    def test_feedback_allowed_when_no_settings(self):
        """No SpeakerFeedbackSettings means feedback is enabled by default."""
        resp = self.client.post(self._url(), self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_feedback_allowed_when_explicitly_enabled(self):
        SpeakerFeedbackSettings.objects.create(
            speaker=self.speaker, event=self.event, feedback_enabled=True
        )
        resp = self.client.post(self._url(), self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_feedback_blocked_when_disabled(self):
        SpeakerFeedbackSettings.objects.create(
            speaker=self.speaker, event=self.event, feedback_enabled=False
        )
        resp = self.client.post(self._url(), self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("disabled", resp.data["detail"])

    def test_feedback_without_event_not_gated(self):
        """Feedback without an event field bypasses the toggle check."""
        SpeakerFeedbackSettings.objects.create(
            speaker=self.speaker, event=self.event, feedback_enabled=False
        )
        payload = self._payload()
        del payload["event"]
        resp = self.client.post(self._url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
