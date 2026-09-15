"""Tests for the feedback app."""

from datetime import timedelta
from io import BytesIO

import qrcode
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from events.models import Event
from feedbacks.models import Feedback
from feedbacks.services import build_feedback_qr_payload
from profiles.models import SpeakerProfile
from profiles.models.speaker_models import SpeakerExperiences

User = get_user_model()

FEEDBACK_RATINGS = {
    "overall_rating": 5,
    "engagement": 4,
    "clarity": 5,
    "content_depth": 4,
    "speaker_knowledge": 5,
    "practical_relevance": 4,
}


def today() -> "object":
    """Return today's local date."""
    return timezone.localdate()


def days_from_today(days: int):
    """Return a date offset from today by ``days``."""
    return today() + timedelta(days=days)


class FeedbackTestMixin:
    """Shared helpers for rate, QR, and list tests."""

    def create_feedback_user(self, username: str, email: str) -> User:
        """Create a verified speaker user with a speaker profile."""
        user = User.objects.create(
            username=username,
            email=email,
            password="testpass123",
            is_email_verified=True,
        )
        SpeakerProfile.objects.create(user_account=user, organization="Web Summit")
        return user

    def create_presentation(
        self,
        speaker_user,
        event_name: str,
        event_date,
        *,
        feedback_enabled: bool = True,
        link_event: Event = None,
    ):
        """Create an experience for the speaker and return it."""
        return SpeakerExperiences.objects.create(
            speaker=SpeakerProfile.objects.get(user_account=speaker_user),
            event_name=event_name,
            event_date=event_date,
            topic="Domain modeling",
            event=link_event,
            feedback_enabled=feedback_enabled,
        )

    def rate_payload(self, **overrides) -> dict:
        """Build a valid rate-submission payload."""
        payload = {"name": "Ada", "comments": "Great talk!", **FEEDBACK_RATINGS}
        payload.update(overrides)
        return payload


class TestFeedback(TestCase):
    """Test feedback models."""

    def test_feedback_creation(self):
        """The six ratings are stored as submitted."""
        feedback = Feedback.objects.create(
            comments="Great session, very informative!",
            **FEEDBACK_RATINGS,
        )
        self.assertEqual(feedback.overall_rating, 5)
        self.assertEqual(feedback.engagement, 4)
        self.assertEqual(feedback.clarity, 5)
        self.assertEqual(feedback.content_depth, 4)
        self.assertEqual(feedback.speaker_knowledge, 5)
        self.assertEqual(feedback.practical_relevance, 4)
        self.assertEqual(feedback.comments, "Great session, very informative!")

    def test_blank_name_is_anonymous(self):
        """A blank name derives is_anonymous to True."""
        feedback = Feedback.objects.create(**FEEDBACK_RATINGS)
        self.assertTrue(feedback.is_anonymous)

    def test_provided_name_is_not_anonymous(self):
        """A supplied name derives is_anonymous to False."""
        feedback = Feedback.objects.create(name="Grace Hopper", **FEEDBACK_RATINGS)
        self.assertFalse(feedback.is_anonymous)
        self.assertEqual(feedback.name, "Grace Hopper")


class FeedbackRateAPITests(FeedbackTestMixin, APITestCase):
    """Tests for the public presentation rating endpoint."""

    def setUp(self):
        """Set up a speaker with past, future, and disabled presentations."""
        self.speaker_user = self.create_feedback_user(
            "rate_speaker", "rate@example.com"
        )
        self.experience = self.create_presentation(
            self.speaker_user, "PastConf", days_from_today(-2)
        )
        self.future_experience = self.create_presentation(
            self.speaker_user, "FutureConf", days_from_today(2)
        )
        self.disabled_experience = self.create_presentation(
            self.speaker_user,
            "DisabledConf",
            days_from_today(-2),
            feedback_enabled=False,
        )
        self.rate_url = reverse(
            "feedbacks:feedback_rate",
            kwargs={"feedback_slug": self.experience.feedback_slug},
        )

    def test_rate_last_weekend_is_accepted_without_auth(self):
        """An anonymous visitor can rate a past presentation."""
        response = self.client.post(self.rate_url, self.rate_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["experience"]["event_name"], "PastConf")
        self.assertEqual(
            response.data["experience"]["feedback_slug"], self.experience.feedback_slug
        )

    def test_rate_is_accepted_on_the_day_of_the_event(self):
        """Feedback opens on (not before) the event date."""
        same_day = self.create_presentation(self.speaker_user, "TodayConf", today())
        url = reverse(
            "feedbacks:feedback_rate",
            kwargs={"feedback_slug": same_day.feedback_slug},
        )
        response = self.client.post(url, self.rate_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rate_is_rejected_before_the_event(self):
        """Feedback for a future presentation is rejected with 403."""
        url = reverse(
            "feedbacks:feedback_rate",
            kwargs={"feedback_slug": self.future_experience.feedback_slug},
        )
        response = self.client.post(url, self.rate_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Feedback.objects.filter(experience=self.future_experience).exists()
        )

    def test_rate_is_rejected_when_speaker_disabled_feedback(self):
        """A speaker who disabled feedback for the experience gets 403."""
        url = reverse(
            "feedbacks:feedback_rate",
            kwargs={"feedback_slug": self.disabled_experience.feedback_slug},
        )
        response = self.client.post(url, self.rate_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_blank_name_submission_is_anonymous(self):
        """Omitting a name stores the feedback as anonymous."""
        speaker = SpeakerProfile.objects.get(user_account=self.speaker_user)
        response = self.client.post(
            self.rate_url, self.rate_payload(name=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        feedback = Feedback.objects.get(experience=self.experience)
        self.assertTrue(response.data["is_anonymous"])
        self.assertEqual(feedback.name, "")
        self.assertEqual(feedback.speaker, speaker)

    def test_named_submission_is_not_anonymous(self):
        """Providing a name stores it and clears the anonymous flag."""
        response = self.client.post(
            self.rate_url, self.rate_payload(name="Grace"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        feedback = Feedback.objects.get(experience=self.experience)
        self.assertFalse(response.data["is_anonymous"])
        self.assertEqual(feedback.name, "Grace")
        self.assertEqual(feedback.speaker.user_account, self.speaker_user)

    def test_rate_does_not_accept_speaker_or_event_in_body(self):
        """Only ratings, name, and comments are writable fields."""
        payload = self.rate_payload()
        payload["speaker"] = "not-needed"
        payload["event"] = "not-needed"
        payload["experience"] = "not-needed"
        response = self.client.post(self.rate_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.filter(experience=self.experience).count(), 1)

    def test_rate_unknown_slug_returns_404(self):
        """An unknown feedback slug returns 404."""
        url = reverse("feedbacks:feedback_rate", kwargs={"feedback_slug": "nope"})
        response = self.client.post(url, self.rate_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Feedback.objects.exists())

    def test_rate_with_invalid_rating_returns_400(self):
        """A rating outside 1..10 is a validation error."""
        response = self.client.post(
            self.rate_url, self.rate_payload(overall_rating=11), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("overall_rating", response.data)

    def test_rate_with_missing_rating_returns_400(self):
        """Omitting a required rating is a validation error."""
        payload = self.rate_payload()
        payload.pop("engagement")
        response = self.client.post(self.rate_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_ip_cannot_resubmit_within_cooldown(self):
        """A second submission from the same IP is throttled with 429."""
        ip = "203.0.113.50"
        first = self.client.post(
            self.rate_url, self.rate_payload(), format="json", REMOTE_ADDR=ip
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        second = self.client.post(
            self.rate_url, self.rate_payload(), format="json", REMOTE_ADDR=ip
        )
        self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_different_ip_can_resubmit(self):
        """A different IP is not blocked by another submitter."""
        self.client.post(
            self.rate_url, self.rate_payload(), format="json", REMOTE_ADDR="203.0.113.1"
        )
        response = self.client.post(
            self.rate_url, self.rate_payload(), format="json", REMOTE_ADDR="203.0.113.2"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.filter(experience=self.experience).count(), 2)

    def test_cooldown_expires_after_window(self):
        """The cooldown resets once the window has passed."""
        self.client.post(
            self.rate_url, self.rate_payload(), format="json", REMOTE_ADDR="203.0.113.9"
        )
        Feedback.objects.filter(experience=self.experience).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        response = self.client.post(
            self.rate_url, self.rate_payload(), format="json", REMOTE_ADDR="203.0.113.9"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_uses_linked_event_start_date_when_available(self):
        """A linked platform event's start time overrides the stored date."""
        event = Event.objects.create(
            title="Linked Conference",
            start_date_time=timezone.now() + timedelta(days=5),
        )
        linked = self.create_presentation(
            self.speaker_user, "LinkedConf", days_from_today(-2), link_event=event
        )
        url = reverse(
            "feedbacks:feedback_rate",
            kwargs={"feedback_slug": linked.feedback_slug},
        )
        response = self.client.post(url, self.rate_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FeedbackQRCodeAPITests(FeedbackTestMixin, APITestCase):
    """Tests for the QR code generation endpoint."""

    def setUp(self):
        """Set up a verified owner and another user."""
        self.owner = self.create_feedback_user("qr_owner", "qr_owner@example.com")
        self.other_user = self.create_feedback_user("qr_other", "qr_other@example.com")
        self.unverified_user = User.objects.create(
            username="qr_unverified",
            email="qr_unverified@example.com",
            password="testpass123",
            is_email_verified=False,
        )
        self.experience = self.create_presentation(
            self.owner, "PastConf", days_from_today(-2)
        )
        self.qr_url = reverse(
            "feedbacks:feedback_qrcode",
            kwargs={"feedback_slug": self.experience.feedback_slug},
        )

    def test_unauthenticated_request_returns_401(self):
        """QR generation requires authentication."""
        response = self.client.get(self.qr_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unverified_speaker_returns_403(self):
        """A verified email is required to generate a QR code."""
        self.client.force_authenticate(self.unverified_user)
        response = self.client.get(self.qr_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_returns_403(self):
        """Only the owner of the presentation may generate its QR code."""
        self.client.force_authenticate(self.other_user)
        response = self.client.get(self.qr_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_gets_png_encoding_rating_url(self):
        """The owner receives a PNG encoding the public rating URL."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.qr_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")

        payload = build_feedback_qr_payload(self.experience.feedback_slug)
        buffer = BytesIO()
        qrcode.make(payload).save(buffer, format="PNG")
        self.assertEqual(response.content, buffer.getvalue())

    def test_unknown_slug_returns_404(self):
        """An unknown feedback slug returns 404."""
        self.client.force_authenticate(self.owner)
        url = reverse("feedbacks:feedback_qrcode", kwargs={"feedback_slug": "nope"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FeedbackListAPITests(FeedbackTestMixin, APITestCase):
    """Tests for the speaker's own feedback list."""

    def setUp(self):
        """Set up a speaker with feedback on two presentations."""
        self.speaker_user = self.create_feedback_user(
            "list_speaker", "list@example.com"
        )
        self.experience = self.create_presentation(
            self.speaker_user, "PastConf", days_from_today(-2)
        )
        self.other_experience = self.create_presentation(
            self.speaker_user, "OtherConf", days_from_today(-5)
        )
        Feedback.objects.create(
            experience=self.experience,
            speaker=self.experience.speaker,
            name="Ada",
            **FEEDBACK_RATINGS,
        )
        Feedback.objects.create(
            experience=self.other_experience,
            speaker=self.other_experience.speaker,
            **FEEDBACK_RATINGS,
        )
        self.list_url = reverse("feedbacks:feedback_list")

    def test_unauthenticated_request_returns_401(self):
        """Listing feedback requires authentication."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_own_feedback(self):
        """The speaker sees only their own feedback."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_can_filter_by_experience(self):
        """An experience filter narrows the results."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.get(
            self.list_url, {"experience": self.experience.feedback_slug}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["experience"]["feedback_slug"],
            self.experience.feedback_slug,
        )

    def test_list_does_not_show_another_speakers_feedback(self):
        """A different speaker sees an empty list."""
        other = self.create_feedback_user("list_other", "listother@example.com")
        self.client.force_authenticate(other)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_unknown_experience_returns_404(self):
        """An unknown experience slug is rejected."""
        self.client.force_authenticate(self.speaker_user)
        response = self.client.get(self.list_url, {"experience": "nope"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FeedbackSummaryAPITests(FeedbackTestMixin, APITestCase):
    """Tests for the aggregate feedback summary on the speaker profile."""

    def setUp(self):
        """Set up feedback across two presentations and an empty speaker."""
        self.speaker_user = self.create_feedback_user("sum_speaker", "sum@example.com")
        self.speaker_profile = SpeakerProfile.objects.get(
            user_account=self.speaker_user
        )
        self.experience = self.create_presentation(
            self.speaker_user, "PastConf", days_from_today(-2)
        )
        self.other_experience = self.create_presentation(
            self.speaker_user, "OtherConf", days_from_today(-5)
        )
        Feedback.objects.create(
            experience=self.experience,
            speaker=self.speaker_profile,
            overall_rating=5,
            engagement=4,
            clarity=5,
            content_depth=4,
            speaker_knowledge=5,
            practical_relevance=4,
        )
        Feedback.objects.create(
            experience=self.other_experience,
            speaker=self.speaker_profile,
            overall_rating=3,
            engagement=2,
            clarity=4,
            content_depth=3,
            speaker_knowledge=5,
            practical_relevance=2,
        )
        self.empty_user = self.create_feedback_user(
            "empty_speaker", "empty@example.com"
        )
        self.detail_url = reverse(
            "speakers:speakers_retrieve_update_delete",
            kwargs={"slug": self.speaker_profile.slug},
        )

    def test_detail_includes_aggregate_averages(self):
        """Averages are rounded across all of the speaker's feedback."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        summary = response.data["feedback_summary"]
        self.assertEqual(summary["total_count"], 2)
        self.assertEqual(summary["overall_rating"]["average"], 4.0)
        self.assertEqual(summary["engagement"]["average"], 3.0)
        self.assertEqual(summary["clarity"]["average"], 4.5)

    def test_detail_includes_score_distribution(self):
        """Distribution buckets count submissions per rating value."""
        response = self.client.get(self.detail_url)
        distribution = response.data["feedback_summary"]["overall_rating"][
            "distribution"
        ]
        self.assertEqual(distribution["5"], 1)
        self.assertEqual(distribution["3"], 1)
        self.assertEqual(distribution["10"], 0)
        self.assertEqual(len(distribution), 10)

    def test_empty_profile_returns_zero_summary(self):
        """A speaker without feedback gets zeros and null averages."""
        url = reverse(
            "speakers:speakers_retrieve_update_delete",
            kwargs={
                "slug": SpeakerProfile.objects.get(user_account=self.empty_user).slug
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        summary = response.data["feedback_summary"]
        self.assertEqual(summary["total_count"], 0)
        self.assertIsNone(summary["overall_rating"]["average"])
        self.assertEqual(summary["overall_rating"]["distribution"]["1"], 0)

    def test_list_has_no_summary(self):
        """The paginated list responses carry no feedback summary."""
        response = self.client.get(reverse("speakers:speakers_list_create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("feedback_summary", response.data[0])
