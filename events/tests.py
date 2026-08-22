"""evetns tests."""

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event, Tag
from events.notifications import notify_speakers_matching_published_cfp
from events.tasks import notify_if_cfp_just_published_task
from profiles.models import Notification, SpeakerProfile, SpeakerSkillTag
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
        from profiles.models import SpeakerProfile

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
        from profiles.models import Notification

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
        from profiles.models import Notification

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


<<<<<<< HEAD
class EventWebsiteNormalizationTests(TestCase):
    """Tests for official website URL normalization used in duplicate detection."""

    def test_strips_scheme_www_and_trailing_slash(self):
        """Equivalent websites normalize to the same value."""
        from events.utils import normalize_event_website

        self.assertEqual(
            normalize_event_website("https://www.PyCon.org/2026/"),
            normalize_event_website("http://pycon.org/2026"),
        )

    def test_empty_website_normalizes_to_empty_string(self):
        """Missing websites compare as empty."""
        from events.utils import normalize_event_website

        self.assertEqual(normalize_event_website(""), "")
        self.assertEqual(normalize_event_website(None), "")


class EventDuplicateDetectionTests(TestCase):
    """Tests for EventQuerySet.find_duplicate."""
=======
class EventListingTests(TestCase):
    """Tests for the public general event listing."""

    def setUp(self):
        """Set up published events with and without an open CFP."""
        self.client = APIClient()
        self.list_url = reverse("events:event-list-create")
        self.market_url = reverse("events:cfp-market")
        self.listed = Event.objects.create(
            title="Dev Conf",
            short_description="A developer conference.",
            description="Talks and workshops.",
            website="https://devconf.example.com",
            cfp_link="https://devconf.example.com/cfp",
            is_active=True,
            accepts_cfp=True,
            cfp_open=True,
        )
        self.showcase_only = Event.objects.create(
            title="Meetup Night",
            short_description="A local meetup.",
            website="https://meetup.example.com",
            is_active=True,
            accepts_cfp=False,
            cfp_open=False,
        )
        self.unpublished = Event.objects.create(
            title="Pending Listing",
            website="https://pending.example.com",
            is_active=False,
        )

    def _listing_by_title(self):
        """Return listing payloads keyed by event title."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {item["title"]: item for item in response.data}

    def test_anonymous_users_can_browse_published_events(self):
        """The public listing returns published events only."""
        by_title = self._listing_by_title()
        self.assertIn(self.listed.title, by_title)
        self.assertIn(self.showcase_only.title, by_title)
        self.assertNotIn(self.unpublished.title, by_title)

    def test_listing_includes_basic_information_and_official_website(self):
        """Listed events include basic info and the official website."""
        payload = self._listing_by_title()[self.listed.title]
        self.assertEqual(payload["short_description"], self.listed.short_description)
        self.assertEqual(payload["description"], self.listed.description)
        self.assertEqual(payload["website"], "https://devconf.example.com")
        self.assertEqual(payload["cfp_link"], "https://devconf.example.com/cfp")
        self.assertIn("date", payload)
        self.assertIn("date_range", payload)

    def test_listing_indicates_whether_cfp_is_currently_open(self):
        """The listing reports CFP status without being the CFP market."""
        by_title = self._listing_by_title()
        self.assertTrue(by_title[self.listed.title]["is_cfp_currently_open"])
        showcase = by_title[self.showcase_only.title]
        self.assertFalse(showcase["is_cfp_currently_open"])

    def test_detail_links_to_official_event_website(self):
        """Event detail includes the official website to visit."""
        url = reverse("events:event-detail", kwargs={"slug": self.listed.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["website"], "https://devconf.example.com")
        self.assertTrue(response.data["is_cfp_currently_open"])

    def test_listing_is_separate_from_cfp_market(self):
        """Events without an open CFP still appear in the general listing."""
        listing_titles = set(self._listing_by_title())
        market = self.client.get(self.market_url)
        self.assertEqual(market.status_code, status.HTTP_200_OK)
        market_titles = {item["title"] for item in market.data}

        self.assertIn(self.showcase_only.title, listing_titles)
        self.assertNotIn(self.showcase_only.title, market_titles)
        self.assertIn(self.listed.title, listing_titles)
        self.assertIn(self.listed.title, market_titles)

    def test_unpublished_event_is_not_publicly_visible_by_slug(self):
        """Anonymous users cannot retrieve an unpublished listing by slug."""
        url = reverse("events:event-detail", kwargs={"slug": self.unpublished.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EventSubmitTests(TestCase):
    """Tests for authenticated users submitting events to the listing."""

    def setUp(self):
        """Set up a submitter, another user, and a published event."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="submitter",
            email="submitter@mail.com",
            password="testpassword",
        )
        self.other_user = User.objects.create(
            username="other_submitter",
            email="other@mail.com",
            password="testpassword",
        )
        self.admin_user = User.objects.create(
            username="event_admin",
            email="event_admin@mail.com",
            password="testpassword",
            is_superuser=True,
        )
        self.published = Event.objects.create(
            title="Published Event",
            website="https://published.example.com",
            is_active=True,
        )
        self.submit_url = reverse("events:event-list-create")
        self.submission_payload = {
            "title": "Community Conf 2026",
            "short_description": "A community conference.",
            "description": "Talks, workshops, and hallway track.",
            "website": "https://communityconf.example.com",
            "cfp_link": "https://communityconf.example.com/cfp",
        }

    def test_unauthenticated_user_cannot_submit(self):
        """POST without authentication is rejected."""
        response = self.client.post(
            self.submit_url, self.submission_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_submit_event(self):
        """An authenticated user can submit an event for listing."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.submit_url, self.submission_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], self.submission_payload["title"])
        self.assertEqual(response.data["website"], self.submission_payload["website"])
        self.assertEqual(response.data["cfp_link"], self.submission_payload["cfp_link"])
        self.assertFalse(response.data["is_active"])
        self.assertEqual(str(response.data["submitted_by"]), str(self.user.id))

        event = Event.objects.get(title="Community Conf 2026")
        self.assertFalse(event.is_active)
        self.assertEqual(event.submitted_by, self.user)
        self.assertEqual(event.website, self.submission_payload["website"])
        self.assertEqual(event.cfp_link, self.submission_payload["cfp_link"])

    def test_submit_without_website_is_rejected(self):
        """Official event URL is required on community submissions."""
        self.client.force_authenticate(user=self.user)
        payload = {**self.submission_payload}
        payload.pop("website")
        response = self.client.post(self.submit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", response.data)

    def test_regular_user_cannot_publish_on_submit(self):
        """Community submissions stay unpublished even if is_active is sent."""
        self.client.force_authenticate(user=self.user)
        payload = {**self.submission_payload, "is_active": True}
        response = self.client.post(self.submit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_active"])
        event = Event.objects.get(title="Community Conf 2026")
        self.assertFalse(event.is_active)

    def test_submitted_event_is_not_publicly_listed(self):
        """Pending submissions do not appear in the public event list."""
        Event.objects.create(
            title="Pending Conf",
            website="https://pending.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        response = self.client.get(self.submit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [event["title"] for event in response.data]
        self.assertIn(self.published.title, titles)
        self.assertNotIn("Pending Conf", titles)

    def test_submitter_can_view_own_pending_event(self):
        """The submitter can retrieve their event before publication."""
        pending = Event.objects.create(
            title="My Pending Conf",
            website="https://mypending.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        url = reverse("events:event-detail", kwargs={"slug": pending.slug})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], pending.title)
        self.assertEqual(response.data["website"], pending.website)

    def test_other_user_cannot_view_pending_event(self):
        """Another user cannot retrieve someone else's unpublished event."""
        pending = Event.objects.create(
            title="Someone Else Conf",
            website="https://someoneelse.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        url = reverse("events:event-detail", kwargs={"slug": pending.slug})
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_event_submit_does_not_create_cfp_submission(self):
        """Submitting an event listing is not an internal CFP submission."""
        from cfps.models import CFPSubmission

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.submit_url, self.submission_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CFPSubmission.objects.count(), 0)

    def test_superuser_can_still_create_published_event(self):
        """Staff can create a published listing directly."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            self.submit_url,
            {
                "title": "Staff Conf",
                "website": "https://staffconf.example.com",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_active"])
        self.assertEqual(str(response.data["submitted_by"]), str(self.admin_user.id))


class CFPMarketAndStatusTests(TestCase):
    """Tests for CFP open/closed status and the CFP Market endpoint."""
>>>>>>> d85917fd (Add submitted_by field and website help text to Event model; enhance admin and serializer functionality for event submissions)

    def setUp(self):
        """Create an existing listed event."""
        self.event = Event.objects.create(
            title="PyCon Ghana 2026",
            website="https://pycon.gh/",
            is_active=True,
        )

    def test_finds_duplicate_by_title_and_website(self):
        """Same title and website is a duplicate, ignoring case and URL noise."""
        duplicate = Event.objects.find_duplicate(
            title="pycon ghana 2026",
            website="http://www.pycon.gh",
        )
        self.assertEqual(duplicate, self.event)

    def test_different_title_same_website_is_not_duplicate(self):
        """A later edition with a different name is not treated as a duplicate."""
        duplicate = Event.objects.find_duplicate(
            title="PyCon Ghana 2027",
            website="https://pycon.gh/",
        )
        self.assertIsNone(duplicate)

    def test_exclude_id_skips_the_event_being_updated(self):
        """Updating an event does not treat it as a duplicate of itself."""
        duplicate = Event.objects.find_duplicate(
            title="PyCon Ghana 2026",
            website="https://pycon.gh/",
            exclude_id=self.event.pk,
        )
        self.assertIsNone(duplicate)


class EventListingTests(TestCase):
    """Tests for the public general event listing."""

    def setUp(self):
        """Set up published events with and without an open CFP."""
        self.client = APIClient()
        self.list_url = reverse("events:event-list-create")
        self.market_url = reverse("events:cfp-market")
        self.listed = Event.objects.create(
            title="Dev Conf",
            short_description="A developer conference.",
            description="Talks and workshops.",
            website="https://devconf.example.com",
            cfp_link="https://devconf.example.com/cfp",
            is_active=True,
            accepts_cfp=True,
            cfp_open=True,
        )
        self.showcase_only = Event.objects.create(
            title="Meetup Night",
            short_description="A local meetup.",
            website="https://meetup.example.com",
            is_active=True,
            accepts_cfp=False,
            cfp_open=False,
        )
        self.unpublished = Event.objects.create(
            title="Pending Listing",
            website="https://pending.example.com",
            is_active=False,
        )

    def _listing_by_title(self):
        """Return listing payloads keyed by event title."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {item["title"]: item for item in response.data}

    def test_anonymous_users_can_browse_published_events(self):
        """The public listing returns published events only."""
        by_title = self._listing_by_title()
        self.assertIn(self.listed.title, by_title)
        self.assertIn(self.showcase_only.title, by_title)
        self.assertNotIn(self.unpublished.title, by_title)

    def test_listing_includes_basic_information_and_official_website(self):
        """Listed events include basic info and the official website."""
        payload = self._listing_by_title()[self.listed.title]
        self.assertEqual(payload["short_description"], self.listed.short_description)
        self.assertEqual(payload["description"], self.listed.description)
        self.assertEqual(payload["website"], "https://devconf.example.com")
        self.assertEqual(payload["cfp_link"], "https://devconf.example.com/cfp")
        self.assertIn("date", payload)
        self.assertIn("date_range", payload)

    def test_listing_indicates_whether_cfp_is_currently_open(self):
        """The listing reports CFP status without being the CFP market."""
        by_title = self._listing_by_title()
        self.assertTrue(by_title[self.listed.title]["is_cfp_currently_open"])
        showcase = by_title[self.showcase_only.title]
        self.assertFalse(showcase["is_cfp_currently_open"])

    def test_detail_links_to_official_event_website(self):
        """Event detail includes the official website to visit."""
        url = reverse("events:event-detail", kwargs={"slug": self.listed.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["website"], "https://devconf.example.com")
        self.assertTrue(response.data["is_cfp_currently_open"])

    def test_listing_is_separate_from_cfp_market(self):
        """Events without an open CFP still appear in the general listing."""
        listing_titles = set(self._listing_by_title())
        market = self.client.get(self.market_url)
        self.assertEqual(market.status_code, status.HTTP_200_OK)
        market_titles = {item["title"] for item in market.data}

        self.assertIn(self.showcase_only.title, listing_titles)
        self.assertNotIn(self.showcase_only.title, market_titles)
        self.assertIn(self.listed.title, listing_titles)
        self.assertIn(self.listed.title, market_titles)

    def test_unpublished_event_is_not_publicly_visible_by_slug(self):
        """Anonymous users cannot retrieve an unpublished listing by slug."""
        url = reverse("events:event-detail", kwargs={"slug": self.unpublished.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EventSubmitTests(TestCase):
    """Tests for submitting, reviewing, and approving event listings."""

    def setUp(self):
        """Set up a submitter, another user, and a published event."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="submitter",
            email="submitter@mail.com",
            password="testpassword",
        )
        self.other_user = User.objects.create(
            username="other_submitter",
            email="other@mail.com",
            password="testpassword",
        )
        self.admin_user = User.objects.create(
            username="event_admin",
            email="event_admin@mail.com",
            password="testpassword",
            is_superuser=True,
        )
        self.published = Event.objects.create(
            title="Published Event",
            website="https://published.example.com",
            is_active=True,
        )
        self.submit_url = reverse("events:event-list-create")
        self.review_url = reverse("events:event-review-list")
        self.submission_payload = {
            "title": "Community Conf 2026",
            "short_description": "A community conference.",
            "description": "Talks, workshops, and hallway track.",
            "website": "https://communityconf.example.com",
            "cfp_url": "https://communityconf.example.com/cfp",
            "cfp_link": "https://communityconf.example.com/cfp",
        }

    def test_unauthenticated_user_cannot_submit(self):
        """POST without authentication is rejected."""
        response = self.client.post(
            self.submit_url, self.submission_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_submit_event(self):
        """An authenticated user can submit an event for listing."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.submit_url, self.submission_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], self.submission_payload["title"])
        self.assertEqual(response.data["website"], self.submission_payload["website"])
        self.assertEqual(response.data["cfp_url"], self.submission_payload["cfp_url"])
        self.assertEqual(response.data["cfp_link"], self.submission_payload["cfp_link"])
        self.assertFalse(response.data["is_active"])
        self.assertEqual(str(response.data["submitted_by"]), str(self.user.id))

        event = Event.objects.get(title="Community Conf 2026")
        self.assertFalse(event.is_active)
        self.assertEqual(event.submitted_by, self.user)
        self.assertEqual(event.website, self.submission_payload["website"])
        self.assertEqual(event.cfp_url, self.submission_payload["cfp_url"])
        self.assertEqual(event.cfp_link, self.submission_payload["cfp_link"])

    def test_submit_without_website_is_rejected(self):
        """Official event URL is required on community submissions."""
        self.client.force_authenticate(user=self.user)
        payload = {**self.submission_payload}
        payload.pop("website")
        response = self.client.post(self.submit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", response.data)

    def test_submit_blank_website_is_rejected(self):
        """Empty or whitespace website values are not accepted."""
        self.client.force_authenticate(user=self.user)
        payload = {**self.submission_payload, "website": ""}
        response = self.client.post(self.submit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", response.data)

    def test_staff_create_without_website_is_rejected(self):
        """Staff-created events also require a website or public event link."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            self.submit_url,
            {"title": "Staff Conf Without Link", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", response.data)

    def test_regular_user_cannot_publish_on_submit(self):
        """Community submissions stay unpublished even if is_active is sent."""
        self.client.force_authenticate(user=self.user)
        payload = {**self.submission_payload, "is_active": True}
        response = self.client.post(self.submit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_active"])
        event = Event.objects.get(title="Community Conf 2026")
        self.assertFalse(event.is_active)

    def test_submitted_event_is_not_publicly_listed(self):
        """Pending submissions do not appear in the public event list."""
        Event.objects.create(
            title="Pending Conf",
            website="https://pending.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        response = self.client.get(self.submit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [event["title"] for event in response.data]
        self.assertIn(self.published.title, titles)
        self.assertNotIn("Pending Conf", titles)

    def test_submitted_event_is_not_publicly_visible_by_slug(self):
        """Anonymous users cannot retrieve an unpublished event by slug."""
        pending = Event.objects.create(
            title="Hidden Conf",
            website="https://hidden.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        url = reverse("events:event-detail", kwargs={"slug": pending.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submitter_can_view_own_pending_event(self):
        """The submitter can retrieve their event before publication."""
        pending = Event.objects.create(
            title="My Pending Conf",
            website="https://mypending.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        url = reverse("events:event-detail", kwargs={"slug": pending.slug})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], pending.title)
        self.assertEqual(response.data["website"], pending.website)

    def test_other_user_cannot_view_pending_event(self):
        """Another user cannot retrieve someone else's unpublished event."""
        pending = Event.objects.create(
            title="Someone Else Conf",
            website="https://someoneelse.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        url = reverse("events:event-detail", kwargs={"slug": pending.slug})
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_submission_is_rejected(self):
        """Submitting the same name and official website is rejected."""
        Event.objects.create(
            title="Community Conf 2026",
            website="https://communityconf.example.com/",
            is_active=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.submit_url, self.submission_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Event.objects.filter(title="Community Conf 2026").count(), 1)

    def test_anonymous_visible_to_returns_published_only(self):
        """Unauthenticated requests have no user identity for submitted_by."""
        pending = Event.objects.create(
            title="Pending Anonymous Check",
            website="https://pending-anon.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        titles = set(
            Event.objects.visible_to(AnonymousUser()).values_list("title", flat=True)
        )
        self.assertIn(self.published.title, titles)
        self.assertNotIn(pending.title, titles)

    def test_superuser_can_still_create_published_event(self):
        """Staff can create a published listing directly."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            self.submit_url,
            {
                "title": "Staff Conf",
                "website": "https://staffconf.example.com",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_active"])
        self.assertEqual(str(response.data["submitted_by"]), str(self.admin_user.id))

    def test_review_list_requires_superuser(self):
        """Regular users cannot list events pending review."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_list_returns_pending_events(self):
        """Superusers can review unpublished submissions."""
        pending = Event.objects.create(
            title="Review Me Conf",
            website="https://reviewme.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [event["id"] for event in response.data]
        self.assertIn(str(pending.id), ids)
        self.assertNotIn(str(self.published.id), ids)

    def test_approve_requires_superuser(self):
        """Regular users cannot approve an event listing."""
        pending = Event.objects.create(
            title="Approve Me Conf",
            website="https://approveme.example.com",
            is_active=False,
            submitted_by=self.user,
        )
        url = reverse("events:event-approve", kwargs={"slug": pending.slug})
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        pending.refresh_from_db()
        self.assertFalse(pending.is_active)

    def test_approved_event_becomes_publicly_visible(self):
        """Approving a submission publishes it and links the official website."""
        pending = Event.objects.create(
            title="Soon Public Conf",
            website="https://soonpublic.example.com",
            cfp_url="https://soonpublic.example.com/cfp",
            is_active=False,
            submitted_by=self.user,
        )
        approve_url = reverse("events:event-approve", kwargs={"slug": pending.slug})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_active"])
        self.assertEqual(response.data["website"], pending.website)

        pending.refresh_from_db()
        self.assertTrue(pending.is_active)

        self.client.force_authenticate(user=None)
        list_response = self.client.get(self.submit_url)
        titles = [event["title"] for event in list_response.data]
        self.assertIn(pending.title, titles)

        detail_url = reverse("events:event-detail", kwargs={"slug": pending.slug})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["website"], pending.website)
        self.assertEqual(detail_response.data["cfp_url"], pending.cfp_url)


class CFPSkillMatchNotificationTests(TestCase):
    """Tests for notifying speakers when a published CFP matches their skills."""

    def setUp(self):
        """Set up speakers, CFP tags, and a closed event."""
        self.python_tag = Tag.objects.create(name="Python")
        self.ai_tag = Tag.objects.create(name="AI")
        self.event = Event.objects.create(
            title="PyData Summit",
            is_active=True,
            cfp_open=False,
        )
        self.event.tags.set([self.python_tag, self.ai_tag])

        self.matching_user = User.objects.create(
            username="py_speaker",
            email="py_speaker@mail.com",
            password="testpassword",
        )
        matching_profile = SpeakerProfile.objects.create(
            user_account=self.matching_user, organization="Org"
        )
        SpeakerSkillTag.objects.create(speaker=matching_profile, name="Python")
        SpeakerSkillTag.objects.create(speaker=matching_profile, name="Data Science")

        self.case_user = User.objects.create(
            username="ai_speaker",
            email="ai_speaker@mail.com",
            password="testpassword",
        )
        case_profile = SpeakerProfile.objects.create(
            user_account=self.case_user, organization="Org"
        )
        SpeakerSkillTag.objects.create(speaker=case_profile, name="ai")

        self.unrelated_user = User.objects.create(
            username="java_speaker",
            email="java_speaker@mail.com",
            password="testpassword",
        )
        unrelated_profile = SpeakerProfile.objects.create(
            user_account=self.unrelated_user, organization="Org"
        )
        SpeakerSkillTag.objects.create(speaker=unrelated_profile, name="Java")
        SpeakerSkillTag.objects.create(speaker=unrelated_profile, name="Spring")

        self.no_skill_user = User.objects.create(
            username="plain_speaker",
            email="plain_speaker@mail.com",
            password="testpassword",
        )
        SpeakerProfile.objects.create(
            user_account=self.no_skill_user, organization="Org"
        )

        self.admin_user = User.objects.create(
            username="cfp_admin",
            email="cfp_admin@mail.com",
            password="testpassword",
            is_superuser=True,
        )
        self.client = APIClient()

    def test_matching_speakers_are_notified(self):
        """Speakers whose skills overlap CFP tags receive a notification."""
        notify_speakers_matching_published_cfp(self.event)
        notified = set(Notification.objects.values_list("user_id", flat=True))
        self.assertIn(self.matching_user.id, notified)
        self.assertIn(self.case_user.id, notified)
        message = Notification.objects.get(user=self.matching_user).message
        self.assertIn(self.event.title, message)
        self.assertIn("Python", message)

    def test_unrelated_speakers_are_not_notified(self):
        """Speakers without overlapping skills do not receive a notification."""
        notify_speakers_matching_published_cfp(self.event)
        notified = set(Notification.objects.values_list("user_id", flat=True))
        self.assertNotIn(self.unrelated_user.id, notified)
        self.assertNotIn(self.no_skill_user.id, notified)

    def test_event_without_tags_notifies_nobody(self):
        """A published CFP with no skill tags notifies no speakers."""
        self.event.tags.clear()
        notify_speakers_matching_published_cfp(self.event)
        self.assertEqual(Notification.objects.count(), 0)

    def test_matching_speakers_receive_email(self):
        """Matching speakers also receive an email notification."""
        notify_speakers_matching_published_cfp(self.event)
        recipients = {email.to[0] for email in mail.outbox}
        self.assertIn(self.matching_user.email, recipients)
        self.assertIn(self.case_user.email, recipients)
        self.assertNotIn(self.unrelated_user.email, recipients)
        self.assertNotIn(self.no_skill_user.email, recipients)

    def test_opening_cfp_via_patch_notifies_matching_speakers(self):
        """PATCH cfp_open False → True notifies speakers with matching skills."""
        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        res = self.client.patch(url, {"cfp_open": True}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        notified = set(Notification.objects.values_list("user_id", flat=True))
        self.assertIn(self.matching_user.id, notified)
        self.assertIn(self.case_user.id, notified)
        self.assertNotIn(self.unrelated_user.id, notified)
        self.assertNotIn(self.no_skill_user.id, notified)

    def test_already_open_cfp_update_does_not_renotify(self):
        """Updating an already-open CFP does not send notifications again."""
        self.event.cfp_open = True
        self.event.save(update_fields=["cfp_open", "updated_at"])

        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        res = self.client.patch(url, {"short_description": "Updated"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 0)

    def test_closing_cfp_does_not_notify(self):
        """Setting cfp_open to False does not notify speakers."""
        self.event.cfp_open = True
        self.event.save(update_fields=["cfp_open", "updated_at"])

        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        res = self.client.patch(url, {"cfp_open": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_event_with_open_cfp_notifies_matching_speakers(self):
        """Creating an event with cfp_open=True notifies matching speakers."""
        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-list-create")
        res = self.client.post(
            url,
            {
                "title": "AI Conf",
                "website": "https://aiconf.example.com",
                "is_active": True,
                "website": "https://aiconf.example.com",
                "cfp_open": True,
                "tags": [str(self.ai_tag.id)],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        notified = set(Notification.objects.values_list("user_id", flat=True))

        self.assertIn(self.case_user.id, notified)
        self.assertNotIn(self.matching_user.id, notified)
        self.assertNotIn(self.unrelated_user.id, notified)

    def test_create_event_with_closed_cfp_does_not_notify(self):
        """Creating an event with cfp_open=False does not notify speakers."""
        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-list-create")
        res = self.client.post(
            url,
            {
                "title": "Closed CFP Conf",
                "website": "https://closedcfp.example.com",
                "is_active": True,
                "website": "https://closedcfp.example.com",
                "cfp_open": False,
                "tags": [str(self.python_tag.id)],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 0)

    @patch("events.views.notify_if_cfp_just_published_task")
    def test_opening_cfp_enqueues_notification_task(self, mock_task):
        """PATCH that opens a CFP enqueues the notification as a background task."""
        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-detail", kwargs={"slug": self.event.slug})
        res = self.client.patch(url, {"cfp_open": True}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        mock_task.enqueue.assert_called_once_with(
            event_id=str(self.event.id),
            was_open=False,
        )

    @patch("events.views.notify_if_cfp_just_published_task")
    def test_create_event_enqueues_notification_task(self, mock_task):
        """Creating an event enqueues the CFP notification as a background task."""
        self.client.force_authenticate(self.admin_user)
        url = reverse("events:event-list-create")
        res = self.client.post(
            url,
            {
                "title": "Queued CFP Conf",
                "website": "https://queuedcfp.example.com",
                "is_active": True,
                "website": "https://queuedcfp.example.com",
                "cfp_open": True,
                "tags": [str(self.ai_tag.id)],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_task.enqueue.assert_called_once_with(
            event_id=res.data["id"],
            was_open=False,
        )


class NotifyIfCFPJustPublishedTaskTests(TestCase):
    """Tests for notify_if_cfp_just_published_task."""

    def setUp(self):
        """Set up an open event and a matching speaker."""
        python_tag = Tag.objects.create(name="Python")
        self.event = Event.objects.create(
            title="Queued Summit",
            is_active=True,
            cfp_open=True,
        )
        self.event.tags.add(python_tag)

        self.speaker_user = User.objects.create(
            username="queued_speaker",
            email="queued_speaker@mail.com",
            password="testpassword",
        )
        profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user, organization="Org"
        )
        SpeakerSkillTag.objects.create(speaker=profile, name="Python")

    def test_missing_event_does_not_raise(self):
        """Enqueueing for an unknown event id logs and returns without error."""
        notify_if_cfp_just_published_task.enqueue(
            event_id=str(uuid4()),
            was_open=False,
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_task_notifies_when_cfp_just_opened(self):
        """The task notifies matching speakers when the CFP just opened."""
        notify_if_cfp_just_published_task.enqueue(
            event_id=str(self.event.id),
            was_open=False,
        )
        self.assertTrue(Notification.objects.filter(user=self.speaker_user).exists())

    def test_task_does_not_notify_when_cfp_was_already_open(self):
        """The task does not notify if the CFP was already open."""
        notify_if_cfp_just_published_task.enqueue(
            event_id=str(self.event.id),
            was_open=True,
        )
        self.assertEqual(Notification.objects.count(), 0)


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
