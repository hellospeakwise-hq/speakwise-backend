"""speaker request app tests."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Event
from organizers.models import OrganizerProfile
from speakerrequests.models import SpeakerRequest
from speakers.models import SpeakerProfile
from users.models import UserRole

User = get_user_model()


class SpeakerRequestTests(APITestCase):
    """speaker request tests."""

    def setUp(self):
        """Set up test data."""
        # Create User Roles
        self.organizer_role = UserRole.objects.create(role="organizer")
        self.speaker_role = UserRole.objects.create(role="speaker")

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

        # Create Profiles
        self.organizer_profile = OrganizerProfile.objects.create(
            user_account=self.organizer_user,
            organization="TechConf",
        )
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            short_bio="Experienced speaker in tech conferences.",
        )

        # Create an Event
        self.event = Event.objects.create(
            title="Test Event",
            organizer=self.organizer_profile,
            start_date="2025-10-10T10:00:00Z",
            end_date="2025-10-10T18:00:00Z",
        )

        # Create a SpeakerRequest for detail/update tests
        self.speaker_request_data = {
            "speaker": self.speaker_profile.id,
            "event": self.event.id,
            "message": "We would like to invite you to speak at our event.",
        }
        self.list_create_url = reverse("speakerrequests:speakerrequest-list-create")

        self.speaker_request = SpeakerRequest.objects.create(
            organizer=self.organizer_profile,
            speaker=self.speaker_profile,
            event=self.event,
            message="Initial request message.",
        )
        self.detail_url = reverse(
            "speakerrequests:speakerrequest-detail", args=[self.speaker_request.id]
        )

    def test_create_speaker_request(self):
        """Test creating a speaker request."""
        # Authenticate as the organizer
        self.client.force_authenticate(user=self.organizer_user)

        response = self.client.post(
            self.list_create_url, self.speaker_request_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SpeakerRequest.objects.count(), 2)
        self.assertEqual(SpeakerRequest.objects.latest("id").status, "PENDING")

    def test_get_speaker_requests(self):
        """Test retrieving speaker requests as the speaker."""
        # Authenticate as the speaker to view their received requests
        self.client.force_authenticate(user=self.speaker_user)

        response = self.client.get(self.list_create_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["message"], "Initial request message.")

    def test_get_speaker_request_detail(self):
        """Test retrieving a single speaker request."""
        # Authenticate as the speaker
        self.client.force_authenticate(user=self.speaker_user)

        response = self.client.get(self.detail_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Initial request message.")

    def test_update_speaker_request(self):
        """Test a speaker accepting a request."""
        # Authenticate as the speaker
        self.client.force_authenticate(user=self.speaker_user)

        update_data = {"status": "ACCEPTED"}
        response = self.client.patch(self.detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.speaker_request.refresh_from_db()
        self.assertEqual(self.speaker_request.status, "ACCEPTED")

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
