"""evetns tests."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event
from users.models import User


class EventAPITestCase(TestCase):
    """Docstring for EventAPITestCase."""

    def setUp(self):
        """Set up test case."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="testuser",
            email="testuser@mail.com",
            password="testpassword",
        )
        self.event_data = {
            "title": "Test Event",
            "short_description": "This is a test event.",
            "website": "https://testevent.com",
            "is_active": True,
        }

        self.event = Event.objects.create(**self.event_data)

    def test_get_event_list(self):
        """Test retrieving the event list."""
        url = reverse("events:event-list-create")
        # Authenticated
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Anonymous (sees active events)
        self.client.force_authenticate(user=None)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_event(self):
        """Test creating a new event."""
        url = reverse("events:event-list-create")
        new_event_data = {
            "title": "New Test Event",
            "short_description": "This is another test event.",
            "website": "https://newevent.com",
        }
        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, new_event_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], new_event_data["title"])

    def test_update_event_unauthorized(self):
        """Test that a regular user cannot update this event."""
        other_user = User.objects.create(
            username="otheruser",
            email="otheruser@mail.com",
            password="testpassword",
        )

        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(url, {"title": "Hacked Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_event_list_with_active_filter(self):
        """Test that event list returns active events."""
        Event.objects.create(
            title="Active Event",
            short_description="Event is active.",
            is_active=True,
        )

        url = reverse("events:event-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 1 from setUp + 1 from here
        self.assertEqual(len(response.data), 2)

    def test_delete_event_unauthorized(self):
        """Test that a regular user cannot delete this event."""
        other_user = User.objects.create(
            username="otheruser2",
            email="otheruser2@mail.com",
            password="testpassword",
        )

        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())


class EventSpeakerDeckToggleTests(TestCase):
    """Tests for EventSpeakerDeckToggleView."""

    def setUp(self):
        """Set up test case with superuser, event, and accepted speakers."""
        self.client = APIClient()

        # Admin user
        self.admin_user = User.objects.create(
            username="toggle_admin",
            email="toggle_admin@mail.com",
            password="testpassword",
            is_superuser=True,
        )

        # Event
        self.event = Event.objects.create(
            title="Toggle Event",
            is_active=True,
            speaker_deck_upload_enabled=False,
        )

        # Speaker with accepted request
        self.speaker_user = User.objects.create(
            username="toggle_speaker",
            email="toggle_speaker@mail.com",
            password="testpassword",
        )
        from speakers.models import SpeakerProfile

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="Speaker Org",
        )
        from speakerrequests.models import SpeakerRequest

        SpeakerRequest.objects.create(
            speaker=self.speaker_profile,
            event=self.event,
            status="accepted",
            message="Welcome!",
        )

        # Non-superuser (should be forbidden)
        self.non_org_user = User.objects.create(
            username="toggle_outsider",
            email="toggle_outsider@mail.com",
            password="testpassword",
        )

        self.toggle_url = reverse(
            "events:event-toggle-speaker-deck", kwargs={"slug": self.event.slug}
        )

    def test_toggle_requires_authentication(self):
        """POST toggle without auth returns 401."""
        res = self.client.post(self.toggle_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_forbidden_for_non_org_user(self):
        """POST toggle by a regular user returns 403."""
        self.client.force_authenticate(self.non_org_user)
        res = self.client.post(self.toggle_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_enables_upload(self):
        """POST toggles from disabled to enabled."""
        self.client.force_authenticate(self.admin_user)
        res = self.client.post(self.toggle_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["speaker_deck_upload_enabled"])
        self.assertIn("enabled", res.data["detail"].lower())

        self.event.refresh_from_db()
        self.assertTrue(self.event.speaker_deck_upload_enabled)

    def test_toggle_disables_upload(self):
        """POST toggles from enabled to disabled."""
        self.event.speaker_deck_upload_enabled = True
        self.event.save()

        self.client.force_authenticate(self.admin_user)
        res = self.client.post(self.toggle_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data["speaker_deck_upload_enabled"])
        self.assertIn("disabled", res.data["detail"].lower())

        self.event.refresh_from_db()
        self.assertFalse(self.event.speaker_deck_upload_enabled)

    def test_toggle_enable_creates_notifications(self):
        """Enabling uploads creates in-app notifications for accepted speakers."""
        from speakers.models import Notification

        self.client.force_authenticate(self.admin_user)
        res = self.client.post(self.toggle_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # One accepted speaker → one notification
        notifications = Notification.objects.filter(user=self.speaker_user)
        self.assertEqual(notifications.count(), 1)
        notif = notifications.first()
        self.assertIn(self.event.title, notif.message)
        self.assertFalse(notif.is_read)

    def test_toggle_disable_does_not_create_notifications(self):
        """Disabling uploads does NOT create notifications."""
        from speakers.models import Notification

        self.event.speaker_deck_upload_enabled = True
        self.event.save()

        self.client.force_authenticate(self.admin_user)
        res = self.client.post(self.toggle_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        notifications = Notification.objects.filter(user=self.speaker_user)
        self.assertEqual(notifications.count(), 0)

    def test_toggle_nonexistent_event_returns_404(self):
        """POST toggle on non-existent event slug returns 404."""
        self.client.force_authenticate(self.admin_user)
        url = reverse(
            "events:event-toggle-speaker-deck", kwargs={"slug": "no-such-event"}
        )
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_speaker_deck_enabled_field_in_event_serializer(self):
        """The speaker_deck_upload_enabled field is exposed in the EventSerializer."""
        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("speaker_deck_upload_enabled", res.data)
        self.assertFalse(res.data["speaker_deck_upload_enabled"])


class CFPMarketAndStatusTests(TestCase):
    """Tests for CFP open/closed status and the CFP Market endpoint."""

    def setUp(self):
        """Set up client and market URL."""
        self.client = APIClient()
        self.market_url = reverse("events:cfp-market")
        self.now = timezone.now()

    def _create_open_cfp_event(self, **overrides):
        """Create an active event with an open CFP."""
        defaults = {
            "title": "Open CFP Event",
            "is_active": True,
            "accepts_cfp": True,
            "cfp_open": True,
            "cfp_link": "https://example.com/cfp",
            "cfp_description": "Talks about Python.",
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)

    def _market_ids(self):
        """Return event IDs from an unauthenticated market GET."""
        response = self.client.get(self.market_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [item["id"] for item in response.data]

    def test_unauthenticated_market_returns_200(self):
        """CFP Market is publicly accessible."""
        response = self.client.get(self.market_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_marked_open_without_dates_appears_in_market(self):
        """Marked open CFP with no dates appears in Market and is currently open."""
        event = self._create_open_cfp_event()
        self.assertTrue(event.is_cfp_currently_open)

        ids = self._market_ids()
        self.assertIn(str(event.id), ids)

        detail = self.client.get(
            reverse("events:event-detail", kwargs={"slug": event.slug})
        )
        self.assertTrue(detail.data["is_cfp_currently_open"])
        self.assertEqual(detail.data["cfp_link"], "https://example.com/cfp")

    def test_cfp_open_false_excluded_from_market(self):
        """Events with cfp_open=False do not appear in the Market."""
        event = self._create_open_cfp_event(cfp_open=False)
        self.assertFalse(event.is_cfp_currently_open)
        self.assertNotIn(str(event.id), self._market_ids())

    def test_past_deadline_excluded_and_save_clears_cfp_open(self):
        """Past deadline excludes from Market and save marks cfp_open False."""
        event = self._create_open_cfp_event()
        # Bypass save so the stored flag stays True while deadline is past.
        Event.objects.filter(pk=event.pk).update(
            cfp_deadline=self.now - timedelta(days=1)
        )
        event.refresh_from_db()
        self.assertTrue(event.cfp_open)
        self.assertFalse(event.is_cfp_currently_open)
        self.assertNotIn(str(event.id), self._market_ids())

        event.save()
        event.refresh_from_db()
        self.assertFalse(event.cfp_open)

    def test_future_open_date_excluded_from_market(self):
        """CFP with a future open date is not yet open."""
        event = self._create_open_cfp_event(
            cfp_open_date=self.now + timedelta(days=7),
            cfp_deadline=self.now + timedelta(days=30),
        )
        self.assertFalse(event.is_cfp_currently_open)
        self.assertNotIn(str(event.id), self._market_ids())

    def test_within_window_included_with_cfp_link(self):
        """CFP within open/deadline window appears with link in Market payload."""
        event = self._create_open_cfp_event(
            title="Window CFP",
            cfp_open_date=self.now - timedelta(days=1),
            cfp_deadline=self.now + timedelta(days=14),
            cfp_link="https://conf.example/cfp",
        )
        self.assertTrue(event.is_cfp_currently_open)

        response = self.client.get(self.market_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match = next(item for item in response.data if item["id"] == str(event.id))
        self.assertEqual(match["cfp_link"], "https://conf.example/cfp")
        self.assertTrue(match["is_cfp_currently_open"])
        self.assertEqual(match["title"], "Window CFP")

    def test_inactive_event_excluded_from_market(self):
        """Inactive events are excluded even when CFP is flagged open."""
        event = self._create_open_cfp_event(is_active=False)
        self.assertTrue(event.is_cfp_currently_open)
        self.assertNotIn(str(event.id), self._market_ids())
