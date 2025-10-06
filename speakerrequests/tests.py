"""speaker request app tests."""

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Event
from organizers.models import OrganizerProfile
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest
from speakers.models import SpeakerProfile
from users.choices import UserRoleChoices
from users.models import UserRole

User = get_user_model()


class SpeakerRequestTests(APITestCase):
    """speaker request tests."""

    def setUp(self):
        """Set up test data."""
        # Create User Roles
        self.organizer_role = UserRole.objects.create(role=UserRoleChoices.ORGANIZER)
        self.speaker_role = UserRole.objects.create(role=UserRoleChoices.SPEAKER)

        # Create Users
        self.organizer_user = User.objects.create(
            username="organizer1",
            email="organizer@mail.com",
            role=self.organizer_role,
        )
        self.organizer_user.set_password("strongpassword")
        self.organizer_user.save()

        self.speaker_user = User.objects.create(
            username="speaker1",
            email="speaker@mail.com",
            role=self.speaker_role,
        )

        self.other_speaker_user = User.objects.create(
            username="speaker2",
            email="speaker2@mail.com",
            role=self.speaker_role,
        )
        self.other_speaker_user.set_password("strongpassword")

        # Create Profiles
        self.organizer_profile = OrganizerProfile.objects.create(
            user_account=self.organizer_user,
            organization="TechConf",
        )
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            short_bio="Experienced speaker in tech conferences.",
        )
        self.other_speaker_profile = SpeakerProfile.objects.create(
            user_account=self.other_speaker_user,
            short_bio="Another speaker.",
        )

        # Create an Event
        self.event = Event.objects.create(
            title="Test Event",
            organizer=self.organizer_profile,
            start_date_time="2025-10-10T10:00:00Z",
            end_date_time="2025-10-10T18:00:00Z",
        )

        # Create a SpeakerRequest for detail/update tests
        self.speaker_request_data = {
            "speaker": self.speaker_profile.id,
            "event": self.event.id,
            "message": "We would like to invite you to speak at our event.",
        }
        self.list_create_url = reverse("speakerrequests:speaker_requests_list_create")

        self.speaker_request = SpeakerRequest.objects.create(
            organizer=self.organizer_profile,
            speaker=self.speaker_profile,
            event=self.event,
            message="Initial request message.",
        )
        self.detail_url = reverse(
            "speakerrequests:speaker_request_retrieve_update_delete",
            args=[self.speaker_request.id],
        )
        self.speaker_list_url = reverse("speakerrequests:speaker_requests_list")
        # This URL seems to be for the SpeakerRequestAcceptView based on the pk argument
        self.speaker_accept_url = reverse(
            "speakerrequests:speaker_request_accept", args=[self.speaker_request.id]
        )

    def test_create_speaker_request(self):
        """Test creating a speaker request."""
        # Authenticate as the organizer
        self.client.force_authenticate(user=self.organizer_user)

        response = self.client.post(
            self.list_create_url, self.speaker_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SpeakerRequest.objects.count(), 2)  # One from setUp, one new
        self.assertEqual(
            SpeakerRequest.objects.latest("id").status,
            RequestStatusChoices.PENDING.value,
        )

    def test_get_speaker_requests(self):
        """Test retrieving speaker requests as the speaker."""
        # Authenticate as the speaker to view their received requests
        self.client.force_authenticate(user=self.speaker_user)

        response = self.client.get(self.speaker_list_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["message"], "Initial request message.")

    def test_unauthorized_access(self):
        """Test unauthorized access to speaker requests."""
        # No authentication provided
        response = self.client.get(self.list_create_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(
            self.list_create_url, self.speaker_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.detail_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(
            self.detail_url, {"status": "ACCEPTED"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SpeakerRequestAcceptViewTests(APITestCase):
    """Tests for the SpeakerRequestAcceptView."""

    def setUp(self):
        """Set up test data."""
        self.organizer_role = UserRole.objects.create(role=UserRoleChoices.ORGANIZER)
        self.speaker_role = UserRole.objects.create(role=UserRoleChoices.SPEAKER)

        self.organizer_user = User.objects.create(
            username="organizer",
            password="password",
            email="organizer@example.com",
            role=self.organizer_role,
        )

        self.speaker_user = User.objects.create(
            username="speaker",
            email="speaker@example.com",
            password="password",
            role=self.speaker_role,
        )

        self.other_speaker_user = User.objects.create(
            username="otherspeaker",
            password="password",
            email="otherspeaker@example.com",
            role=self.speaker_role,
        )

        self.organizer_profile = OrganizerProfile.objects.create(
            user_account=self.organizer_user
        )
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user
        )

        self.event = Event.objects.create(
            title="Test Event",
            organizer=self.organizer_profile,
            start_date_time="2025-10-10T10:00:00Z",
            end_date_time="2025-10-10T18:00:00Z",
        )

        self.speaker_request = SpeakerRequest.objects.create(
            organizer=self.organizer_profile,
            speaker=self.speaker_profile,
            event=self.event,
            status=RequestStatusChoices.PENDING,
            message="Please speak at our event.",
        )
        self.url = reverse(
            "speakerrequests:speaker_request_accept", args=[self.speaker_request.pk]
        )

    def test_speaker_can_accept_request(self):
        """Test that a speaker can accept a pending request."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.patch(self.url, {"status": "accepted"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.speaker_request.refresh_from_db()
        self.assertEqual(self.speaker_request.status, RequestStatusChoices.ACCEPTED)
        self.assertEqual(len(mail.outbox), 1)
        assert "has been Accepted" in mail.outbox[0].subject

    def test_speaker_can_reject_request(self):
        """Test that a speaker can reject a pending request."""
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.patch(self.url, {"status": "rejected"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.speaker_request.refresh_from_db()
        self.assertEqual(self.speaker_request.status, RequestStatusChoices.REJECTED)
        self.assertEqual(len(mail.outbox), 1)
        assert "has been Declined" in mail.outbox[0].subject

    def test_cannot_update_non_pending_request(self):
        """Test that a request not in 'pending' status cannot be updated."""
        self.speaker_request.status = RequestStatusChoices.ACCEPTED
        self.speaker_request.save()
        self.client.force_authenticate(user=self.speaker_user)
        response = self.client.patch(self.url, {"status": "rejected"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "You can only update requests that are in PENDING status.",
        )
