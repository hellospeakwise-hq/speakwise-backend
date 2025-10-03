"""speaker request app tests."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate
from speakerrequests.models import SpeakerRequest
from speakers.models import SpeakerProfile
from organizers.models import OrganizerProfile
from django.contrib.auth import get_user_model
from users.models import UserRole
User = get_user_model()




class SpeakerRequestTests(APITestCase):
    """speaker request tests."""

    def setUp(self):
        """Set up test data."""
        self.organizer_user = User.objects.create(
            username="organizer1",
            email="organizer@mail.com",
            role=UserRole.objects.create(role="organizer"),
        )
        self.organizer_user.set_password("strongpassword")
        self.organizer_user.save()
        self.speaker_user = User.objects.create(
            username="speaker1",
            email="speaker@mail.com",
            role=UserRole.objects.create(role="speaker"),
        )
        self.speaker_user.set_password("strongpassword")
        self.speaker_user.save()
        self.organizer_profile = OrganizerProfile.objects.create(
            user_account=self.organizer_user,
            organization="TechConf",
        )
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            short_bio="Experienced speaker in tech conferences.",
        )
        self.speaker_request_data = {
            "speaker": self.speaker_profile.id,
            "event": 1,  # Assuming event with ID 1 exists
            "message": "We would like to invite you to speak at our event.",
            "status": "pending",
        }
        self.url = reverse("speakerrequests:speaker_requests_list_create")
        self.client.login(username="organizer1", password="strongpassword")
        self.speaker_request = SpeakerRequest.objects.create(
            organizer=self.organizer_profile,
            speaker=self.speaker_profile,
            event_id=1,
            message="Initial request message.",
            status="pending",
        )

    def test_create_speaker_request(self):
        """Test creating a speaker request."""
        # authenticated as organizer
        self.client.force_login(self.organizer_user)
        response = self.client.post(self.url, self.speaker_request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SpeakerRequest.objects.count(), 2)
        self.assertEqual(SpeakerRequest.objects.latest('id').message, "We would like to invite you to speak at our event.")

    def test_get_speaker_requests(self):
        """Test retrieving speaker requests."""
        self.client.force_login(self.organizer_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], "Initial request message.")

    def test_get_speaker_request_detail(self):
        """Test retrieving a single speaker request."""
        self.client.force_login(self.organizer_user)
        url = reverse("speakerrequest-detail", args=[self.speaker_request.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Initial request message.")

    def test_update_speaker_request(self):
        """Test updating a speaker request."""
        self.client.force_login(self.speaker_user)
        url = reverse("speakerrequest:speaker_request_retrieve_update_delete", args=[self.speaker_request.id])
        update_data = {"message": "Updated request message.", "status": "accepted"}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.speaker_request.refresh_from_db()
        self.assertEqual(self.speaker_request.message, "Updated request message.")
        self.assertEqual(self.speaker_request.status, "accepted")

    def test_unauthorized_access(self):
        """Test unauthorized access to speaker requests."""
        self.client.force_login(self.speaker_user)
        self.client.logout()
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.url, self.speaker_request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse("speakerrequest-detail", args=[self.speaker_request.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(url, {"message": "Should not update."}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        """Clean up after tests."""
        self.client.logout()
        User.objects.all().delete()
        OrganizerProfile.objects.all().delete()
        SpeakerProfile.objects.all().delete()
        SpeakerRequest.objects.all().delete()