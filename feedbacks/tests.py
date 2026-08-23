"""Tests for the feedback app."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from events.models import Event
from feedbacks.models import EventFeedbackPreference, Feedback
from profiles.models import SpeakerProfile
from speakerrequests.models import SpeakerRequest

User = get_user_model()

FEEDBACK_RATINGS = {
    "overall_rating": 5,
    "engagement": 4,
    "clarity": 5,
    "content_depth": 4,
    "speaker_knowledge": 5,
    "practical_relevance": 4,
}


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

        # Create a feedback instance
        self.feedback = Feedback.objects.create(
            comments="Great session, very informative!",
            is_anonymous=False,
            is_attendee=True,
            **FEEDBACK_RATINGS,
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


class FeedbackTestDataMixin:
    """Shared setup for feedback preference and gating tests."""

    def create_feedback_test_data(self):
        """Create a speaker accepted for an event, plus a rejected speaker."""
        self.speaker_user = User.objects.create(
            username="preference_speaker",
            email="preference_speaker@example.com",
            password="testpass123",
        )
        self.rejected_user = User.objects.create(
            username="rejected_speaker",
            email="rejected_speaker@example.com",
            password="testpass123",
        )
        self.no_profile_user = User.objects.create(
            username="no_profile_user",
            email="no_profile@example.com",
            password="testpass123",
        )

        # UserManager.create auto-creates a SpeakerProfile per user; remove those
        # so the view's .first() lookup resolves to the profiles created below
        # (and so no_profile_user genuinely has no profile).
        SpeakerProfile.objects.filter(
            user_account__in=[
                self.speaker_user,
                self.rejected_user,
                self.no_profile_user,
            ]
        ).delete()

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="Preference Org",
        )
        self.rejected_profile = SpeakerProfile.objects.create(
            user_account=self.rejected_user,
            organization="Rejected Org",
        )

        self.event = Event.objects.create(
            title="Feedback Conference",
            is_active=True,
        )
        self.other_event = Event.objects.create(
            title="Other Conference",
            is_active=True,
        )

        SpeakerRequest.objects.create(
            speaker=self.speaker_profile,
            event=self.event,
            status="accepted",
            message="Welcome!",
        )
        SpeakerRequest.objects.create(
            speaker=self.rejected_profile,
            event=self.event,
            status="rejected",
            message="Sorry.",
        )


class EventFeedbackPreferenceModelTests(FeedbackTestDataMixin, TestCase):
    """Tests for the EventFeedbackPreference model."""

    def setUp(self):
        """Set up test data."""
        self.create_feedback_test_data()

    def test_feedback_is_enabled_by_default(self):
        """A new preference record defaults to feedback enabled."""
        preference = EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event
        )
        self.assertTrue(preference.is_feedback_enabled)

    def test_speaker_and_event_are_unique_together(self):
        """A speaker can only have one preference record per event."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            EventFeedbackPreference.objects.create(
                speaker=self.speaker_profile, event=self.event
            )

    def test_str_shows_state_speaker_and_event(self):
        """String representation includes state, speaker and event."""
        preference = EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event, is_feedback_enabled=False
        )
        self.assertEqual(
            str(preference),
            f"Feedback disabled for {self.speaker_profile} at {self.event}",
        )

    def test_is_feedback_enabled_for_defaults_to_true_without_record(self):
        """Without a preference record feedback is considered open."""
        self.assertTrue(
            EventFeedbackPreference.objects.is_enabled_for(
                self.speaker_profile, self.event
            )
        )

    def test_is_feedback_enabled_for_respects_disabled_record(self):
        """An explicit disabled record closes feedback."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event, is_feedback_enabled=False
        )
        self.assertFalse(
            EventFeedbackPreference.objects.is_enabled_for(
                self.speaker_profile, self.event
            )
        )


class EventFeedbackPreferenceAPITests(FeedbackTestDataMixin, APITestCase):
    """Tests for the event feedback preference endpoint."""

    def setUp(self):
        """Set up test data."""
        self.create_feedback_test_data()
        self.url = reverse(
            "feedbacks:event_feedback_preference",
            kwargs={"event_id": self.event.id},
        )

    def test_unauthenticated_get_returns_401(self):
        """GET without authentication is rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_put_returns_401(self):
        """PUT without authentication is rejected."""
        response = self.client.put(self.url, {"is_feedback_enabled": False})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_enabled_by_default(self):
        """Without a saved preference the endpoint reports feedback enabled."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_feedback_enabled"])
        self.assertEqual(str(response.data["event"]), str(self.event.id))

    def test_get_returns_saved_preference(self):
        """A saved disabled preference is reflected in the response."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event, is_feedback_enabled=False
        )
        self.client.force_authenticate(self.speaker_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_feedback_enabled"])

    def test_put_disables_feedback(self):
        """PUT with false closes feedback for the event."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.put(self.url, {"is_feedback_enabled": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_feedback_enabled"])
        self.assertFalse(
            EventFeedbackPreference.objects.is_enabled_for(
                self.speaker_profile, self.event
            )
        )

    def test_put_reenables_feedback(self):
        """PUT with true reopens feedback and keeps a single record."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event, is_feedback_enabled=False
        )
        self.client.force_authenticate(self.speaker_user)
        response = self.client.put(self.url, {"is_feedback_enabled": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_feedback_enabled"])
        self.assertEqual(
            EventFeedbackPreference.objects.filter(
                speaker=self.speaker_profile, event=self.event
            ).count(),
            1,
        )
        self.assertTrue(
            EventFeedbackPreference.objects.is_enabled_for(
                self.speaker_profile, self.event
            )
        )

    def test_put_is_idempotent(self):
        """Repeating the same PUT keeps the same state."""
        self.client.force_authenticate(self.speaker_user)
        self.client.put(self.url, {"is_feedback_enabled": False})
        response = self.client.put(self.url, {"is_feedback_enabled": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_feedback_enabled"])

    def test_put_without_body_returns_400(self):
        """PUT without is_feedback_enabled is a validation error."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.put(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_feedback_enabled", response.data)

    def test_put_with_invalid_value_returns_400(self):
        """PUT with a non-boolean value is a validation error."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.put(self.url, {"is_feedback_enabled": "maybe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_without_speaker_profile_returns_403(self):
        """A user with no speaker profile may not manage preferences."""
        self.client.force_authenticate(self.no_profile_user)
        response = self.client.put(self.url, {"is_feedback_enabled": False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_accepted_speaker_returns_403(self):
        """A speaker without an accepted request may not manage preferences."""
        self.client.force_authenticate(self.rejected_user)
        response = self.client.put(self.url, {"is_feedback_enabled": False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            EventFeedbackPreference.objects.filter(
                speaker=self.rejected_profile
            ).exists()
        )

    def test_accepted_speaker_for_other_event_returns_403(self):
        """Acceptance for one event grants no access to another event."""
        other_url = reverse(
            "feedbacks:event_feedback_preference",
            kwargs={"event_id": self.other_event.id},
        )
        self.client.force_authenticate(self.speaker_user)
        response = self.client.put(other_url, {"is_feedback_enabled": False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_event_returns_404(self):
        """An unknown event id returns 404."""
        url = reverse(
            "feedbacks:event_feedback_preference",
            kwargs={"event_id": "00000000-0000-0000-0000-000000000000"},
        )
        self.client.force_authenticate(self.speaker_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FeedbackSubmissionGatingTests(FeedbackTestDataMixin, APITestCase):
    """Tests for feedback submission being gated by the speaker's preference."""

    def setUp(self):
        """Set up test data."""
        self.create_feedback_test_data()
        self.url = reverse("feedbacks:feedbacks_list_create")

    def _feedback_payload(self, **overrides):
        """Build a valid feedback submission payload."""
        payload = {
            "speaker": str(self.speaker_profile.id),
            "event": str(self.event.id),
            "comments": "Great talk!",
            **FEEDBACK_RATINGS,
        }
        payload.update(overrides)
        return payload

    def test_feedback_is_accepted_without_preference_record(self):
        """Feedback is open by default when the speaker has not opted out."""
        response = self.client.post(self.url, self._feedback_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Feedback.objects.filter(
                speaker=self.speaker_profile, event=self.event
            ).count(),
            1,
        )

    def test_feedback_is_accepted_when_explicitly_enabled(self):
        """Feedback is accepted when the speaker explicitly enabled it."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event, is_feedback_enabled=True
        )
        response = self.client.post(self.url, self._feedback_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_feedback_is_rejected_when_disabled(self):
        """Feedback is rejected with 403 when the speaker closed it."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile, event=self.event, is_feedback_enabled=False
        )
        response = self.client.post(self.url, self._feedback_payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Feedback.objects.filter(speaker=self.speaker_profile).exists())

    def test_disabling_one_event_does_not_block_another(self):
        """Closing feedback for one event leaves other events open."""
        EventFeedbackPreference.objects.create(
            speaker=self.speaker_profile,
            event=self.other_event,
            is_feedback_enabled=False,
        )
        response = self.client.post(self.url, self._feedback_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_feedback_without_event_returns_400(self):
        """Event is required so the toggle cannot be bypassed by omitting it."""
        payload = self._feedback_payload()
        payload.pop("event")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("event", response.data)

    def test_feedback_with_unknown_event_returns_400(self):
        """An event id that does not exist is a validation error."""
        payload = self._feedback_payload(event="00000000-0000-0000-0000-000000000000")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
