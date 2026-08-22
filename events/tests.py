"""evetns tests."""

from django.test import TestCase
from django.urls import reverse
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


class EventSubmissionWorkflowTests(TestCase):
    """Tests for submitting, reviewing, and approving event listings."""

    def setUp(self):
        """Set up users and a published event."""
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
        self.assertFalse(response.data["is_active"])
        self.assertEqual(str(response.data["submitted_by"]), str(self.user.id))

        event = Event.objects.get(title="Community Conf 2026")
        self.assertFalse(event.is_active)
        self.assertEqual(event.submitted_by, self.user)
        self.assertEqual(event.website, self.submission_payload["website"])
        self.assertEqual(event.cfp_url, self.submission_payload["cfp_url"])

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
        """The user who submitted an event can retrieve it before approval."""
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
        """A different user cannot retrieve someone else's unpublished event."""
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
