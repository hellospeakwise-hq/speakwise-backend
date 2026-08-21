"""evetns tests."""

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event, Tag
from events.notifications import notify_speakers_matching_published_cfp
from speakers.models import Notification, SpeakerProfile, SpeakerSkillTag
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
                "is_active": True,
                "cfp_open": True,
                "tags": [str(self.ai_tag.id)],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        notified = self._notification_users()
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
                "is_active": True,
                "cfp_open": False,
                "tags": [str(self.python_tag.id)],
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 0)
