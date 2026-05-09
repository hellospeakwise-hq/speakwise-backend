"""CFP view tests."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from cfps.choices import AudienceLevelChoices, CFPStatusChoices, TalkTypeChoices
from cfps.models import CFPSubmission
from events.models import Country, Event, Location
from organizations.models import Organization, OrganizationMembership
from users.models import User

CFP_PAYLOAD = {
    "talk_type": TalkTypeChoices.SHORT,
    "audience": AudienceLevelChoices.ALL,
    "category": "frontend",
    "elevator_pitch": "A great talk pitch.",
    "abstract": "Full abstract of the talk.",
}


class CFPSubmissionListCreateViewTest(TestCase):
    """Test POST and GET /api/events/<slug>/cfp/."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.organizer_user = User.objects.create(
            username="organizer", email="organizer@test.com", password="testpass"
        )
        self.speaker_user = User.objects.create(
            username="speaker", email="speaker@test.com", password="testpass"
        )
        self.other_user = User.objects.create(
            username="other", email="other@test.com", password="testpass"
        )
        self.org = Organization.objects.create(
            name="TestOrg", email="testorg@test.com", created_by=self.organizer_user
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.organizer_user,
            role="ADMIN",
            added_by=self.organizer_user,
        )
        self.event = Event.objects.create(
            title="PyCon View Test",
            description="Event for view tests",
            location=Location.objects.create(
                venue="Venue",
                address="Addr",
                city="City",
                state="State",
                country=Country.objects.create(name="Ghana"),
            ),
            organizer=self.org,
        )
        self.url = reverse("cfp:cfp-list-create", kwargs={"slug": self.event.slug})

    def test_unauthenticated_cannot_submit(self):
        """Test that unauthenticated users cannot submit a CFP."""
        response = self.client.post(self.url, CFP_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_submit(self):
        """Test that an authenticated user can submit a CFP."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.post(self.url, CFP_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 201)

    def test_multiple_submissions_same_event_allowed(self):
        """Test that a user can submit more than one CFP to the same event."""
        self.client.force_authenticate(user=self.speaker_user)
        r1 = self.client.post(self.url, CFP_PAYLOAD, format="json")
        r2 = self.client.post(self.url, CFP_PAYLOAD, format="json")
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertNotEqual(r1.data["id"], r2.data["id"])

    def test_submission_response_includes_event_slug_and_title(self):
        """Test that the submission response includes event_slug and event_title."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.post(self.url, CFP_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("event_slug", response.data)
        self.assertIn("event_title", response.data)
        self.assertEqual(response.data["event_slug"], self.event.slug)
        self.assertEqual(response.data["event_title"], self.event.title)

    def test_submission_with_new_fields(self):
        """Test that new CFP fields (title, duration, language, etc.) are accepted."""
        self.client.force_authenticate(user=self.speaker_user)
        payload = {
            **CFP_PAYLOAD,
            "title": "My Talk Title",
            "duration": 30,
            "language": "French",
            "outline": "Intro, body, conclusion.",
            "is_first_time_speaker": True,
            "travel_support_needed": True,
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "My Talk Title")
        self.assertEqual(response.data["duration"], 30)
        self.assertEqual(response.data["language"], "French")
        self.assertTrue(response.data["is_first_time_speaker"])
        self.assertTrue(response.data["travel_support_needed"])

    def test_submitter_sees_only_own_submission(self):
        """Test that a submitter only sees their own submission."""
        CFPSubmission.objects.create(
            event=self.event, submitter=self.speaker_user, **CFP_PAYLOAD
        )
        CFPSubmission.objects.create(
            event=self.event, submitter=self.other_user, **CFP_PAYLOAD
        )
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_organizer_sees_all_submissions(self):
        """Test that an organizer sees all submissions for the event."""
        CFPSubmission.objects.create(
            event=self.event, submitter=self.speaker_user, **CFP_PAYLOAD
        )
        CFPSubmission.objects.create(
            event=self.event, submitter=self.other_user, **CFP_PAYLOAD
        )
        self.client.force_authenticate(user=self.organizer_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_returns_404_for_nonexistent_event(self):
        """Test that a 404 is returned for a nonexistent event."""
        self.client.force_authenticate(user=self.speaker_user)
        url = reverse("cfp:cfp-list-create", kwargs={"slug": "does-not-exist"})
        response = self.client.post(url, CFP_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 404)


class CFPSubmissionDetailViewTest(TestCase):
    """Test GET, PATCH, DELETE /api/cfp/<id>/."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.organizer_user = User.objects.create(
            username="org_detail", email="orgdetail@test.com", password="testpass"
        )
        self.speaker_user = User.objects.create(
            username="spk_detail", email="spkdetail@test.com", password="testpass"
        )
        self.unrelated_user = User.objects.create(
            username="unrelated", email="unrelated@test.com", password="testpass"
        )
        self.org = Organization.objects.create(
            name="DetailOrg", email="detailorg@test.com", created_by=self.organizer_user
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.organizer_user,
            role="ADMIN",
            added_by=self.organizer_user,
        )
        self.event = Event.objects.create(
            title="Detail Event",
            description="Event for detail tests",
            location=Location.objects.create(
                venue="Venue",
                address="Addr",
                city="City",
                state="State",
                country=Country.objects.create(name="Nigeria"),
            ),
            organizer=self.org,
        )
        self.submission = CFPSubmission.objects.create(
            event=self.event, submitter=self.speaker_user, **CFP_PAYLOAD
        )
        self.url = reverse("cfp:cfp-detail", kwargs={"pk": self.submission.id})

    def test_submitter_can_retrieve(self):
        """Test that the submitter can retrieve their submission."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_organizer_can_retrieve(self):
        """Test that an organizer can retrieve a submission."""
        self.client.force_authenticate(user=self.organizer_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unrelated_user_cannot_retrieve(self):
        """Test that an unrelated user cannot retrieve a submission."""
        self.client.force_authenticate(user=self.unrelated_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_submitter_can_edit_while_pending(self):
        """Test that the submitter can edit their submission while it is pending."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.patch(
            self.url, {"elevator_pitch": "Updated pitch."}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.elevator_pitch, "Updated pitch.")

    def test_submitter_cannot_edit_after_accepted(self):
        """Test that the submitter cannot edit their submission after it is accepted."""
        self.submission.status = CFPStatusChoices.ACCEPTED
        self.submission.save()
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.patch(
            self.url, {"elevator_pitch": "Too late."}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_submitter_can_delete_while_pending(self):
        """Test that the submitter can delete their submission while it is pending."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(CFPSubmission.objects.filter(id=self.submission.id).exists())

    def test_submitter_cannot_delete_after_accepted(self):
        """Test that the submitter cannot delete their submission after it is accepted."""
        self.submission.status = CFPStatusChoices.ACCEPTED
        self.submission.save()
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_access(self):
        """Test that unauthenticated users cannot access a submission."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class CFPStatusUpdateViewTest(TestCase):
    """Test PATCH /api/cfp/<id>/status/."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.organizer_user = User.objects.create(
            username="org_status", email="orgstatus@test.com", password="testpass"
        )
        self.speaker_user = User.objects.create(
            username="spk_status", email="spkstatus@test.com", password="testpass"
        )
        self.org = Organization.objects.create(
            name="StatusOrg", email="statusorg@test.com", created_by=self.organizer_user
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.organizer_user,
            role="ADMIN",
            added_by=self.organizer_user,
        )
        self.event = Event.objects.create(
            title="Status Event",
            description="Event for status tests",
            location=Location.objects.create(
                venue="Venue",
                address="Addr",
                city="City",
                state="State",
                country=Country.objects.create(name="Kenya"),
            ),
            organizer=self.org,
        )
        self.submission = CFPSubmission.objects.create(
            event=self.event, submitter=self.speaker_user, **CFP_PAYLOAD
        )
        self.url = reverse("cfp:cfp-status-update", kwargs={"pk": self.submission.id})

    @patch("cfps.views.CFPEmailService.send_status_notification")
    def test_organizer_can_accept(self, mock_email):
        """Test that an organizer can accept a submission."""
        self.client.force_authenticate(user=self.organizer_user)
        response = self.client.patch(self.url, {"status": "accepted"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, CFPStatusChoices.ACCEPTED)
        mock_email.assert_called_once_with(self.submission)

    @patch("cfps.views.CFPEmailService.send_status_notification")
    def test_organizer_can_reject(self, mock_email):
        """Test that an organizer can reject a submission."""
        self.client.force_authenticate(user=self.organizer_user)
        response = self.client.patch(self.url, {"status": "rejected"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, CFPStatusChoices.REJECTED)
        mock_email.assert_called_once()

    @patch("cfps.views.CFPEmailService.send_status_notification")
    def test_submitter_cannot_update_status(self, mock_email):
        """Test that a submitter cannot update the status of their own submission."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.patch(self.url, {"status": "accepted"}, format="json")
        self.assertEqual(response.status_code, 403)
        mock_email.assert_not_called()


class MyCFPSubmissionsViewTest(TestCase):
    """Test GET /api/cfp/mine/."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.speaker = User.objects.create(
            username="mine_speaker", email="mine@test.com", password="testpass"
        )
        self.other = User.objects.create(
            username="mine_other", email="mine_other@test.com", password="testpass"
        )
        self.org = Organization.objects.create(
            name="MineOrg", email="mineorg@test.com", created_by=self.speaker
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.speaker,
            role="ADMIN",
            added_by=self.speaker,
        )
        self.event_a = Event.objects.create(
            title="Mine Event A",
            description="desc",
            location=Location.objects.create(
                venue="V",
                address="A",
                city="C",
                state="S",
                country=Country.objects.create(name="MineCountry"),
            ),
            organizer=self.org,
        )
        self.event_b = Event.objects.create(
            title="Mine Event B",
            description="desc",
            location=Location.objects.create(
                venue="V2",
                address="A2",
                city="C2",
                state="S2",
                country=Country.objects.create(name="MineCountry2"),
            ),
            organizer=self.org,
        )
        self.sub_a = CFPSubmission.objects.create(
            event=self.event_a, submitter=self.speaker, **CFP_PAYLOAD
        )
        self.sub_b = CFPSubmission.objects.create(
            event=self.event_b, submitter=self.speaker, **CFP_PAYLOAD
        )
        # submission by a different user — should not appear
        CFPSubmission.objects.create(
            event=self.event_a, submitter=self.other, **CFP_PAYLOAD
        )
        self.url = reverse("cfp:cfp-mine")

    def test_unauthenticated_cannot_access(self):
        """Test that unauthenticated users cannot access the mine endpoint."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_returns_only_own_submissions(self):
        """Test that only the authenticated user's own submissions are returned."""
        self.client.force_authenticate(user=self.speaker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        ids = {s["id"] for s in response.data}
        self.assertIn(str(self.sub_a.id), ids)
        self.assertIn(str(self.sub_b.id), ids)
        self.assertEqual(len(response.data), 2)

    def test_other_user_sees_only_their_own(self):
        """Test that a different user only sees their own submissions."""
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_response_includes_event_slug_and_title(self):
        """Test that each result includes event_slug and event_title."""
        self.client.force_authenticate(user=self.speaker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for item in response.data:
            self.assertIn("event_slug", item)
            self.assertIn("event_title", item)
            self.assertIsNotNone(item["event_slug"])
            self.assertIsNotNone(item["event_title"])
