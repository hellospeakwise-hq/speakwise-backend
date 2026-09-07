"""Events tests."""

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
            "description": "This is a test event.",
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
            "description": "This is another test event.",
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
            description="Event is active.",
            website="https://activeevent.example.com",
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


class EventListingTests(TestCase):
    """Tests for the public general event listing."""

    def setUp(self):
        """Set up published events with and without an open CFP."""
        self.client = APIClient()
        self.list_url = reverse("events:event-list-create")
        self.market_url = reverse("events:cfp-market")
        self.listed = Event.objects.create(
            title="Dev Conf",
            description="Talks and workshops.",
            website="https://devconf.example.com",
            cfp_link="https://devconf.example.com/cfp",
            is_active=True,
            cfp_open=True,
        )
        self.showcase_only = Event.objects.create(
            title="Meetup Night",
            description="A local meetup.",
            website="https://meetup.example.com",
            is_active=True,
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
        self.assertEqual(payload["description"], self.listed.description)
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
        self.submission_payload = {
            "title": "Community Conf 2026",
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
        url = reverse("events:events-mine")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get("title"), pending.title)
        self.assertEqual(response.data[0].get("website"), pending.website)

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
            Event.objects.filter(is_active=True).values_list("title", flat=True)
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
            "website": "https://opencfp.example.com",
            "is_active": True,
            "cfp_open": True,
            "cfp_link": "https://example.com/cfp",
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
