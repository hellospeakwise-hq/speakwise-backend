"""Sessions tests."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Event
from eventsessions.models import Session, SessionVenue, Track
from eventsessions.serializers import SessionSerializer
from organizations.models import Organization, OrganizationMembership
from users.models import User


class SessionAPITestCase(APITestCase):
    """Test session API."""

    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

        # Create organization
        self.org = Organization.objects.create(name="Test Org", email="org@example.com")

        # Make user an admin of the organization
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role="ADMIN"
        )

        # Create event
        self.event = Event.objects.create(
            title="Test Event",
            organizer=self.org,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=1),
        )

        # Create track
        self.track = Track.objects.create(
            name="Test Track", color="#FF0000", description="Test Track Description"
        )

        # Create venue
        self.venue = SessionVenue.objects.create(
            name="Test Venue",
            capacity=100,
            location_notes="Some notes",
            virtual_url="https://example.com",
        )

        # Create session
        self.session = Session.objects.create(
            event=self.event,
            track=self.track,
            title="Test Session",
            abstract="Test Abstract",
            venue=self.venue,
            session_type="Talk",
            level="Beginner",
            status="Confirmed",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            max_attendees=50,
        )

    def test_list_sessions(self):
        """Test listing sessions for an event."""
        url = reverse("sessions:session-list", kwargs={"event_slug": self.event.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.session.title)

    def test_create_session(self):
        """Test creating a new session."""
        url = reverse("sessions:session-list", kwargs={"event_slug": self.event.slug})
        data = {
            "title": "New Session",
            "abstract": "New Abstract",
            "track": {
                "name": "New Track",
                "color": "#00FF00",
                "description": "New track desc",
            },
            "venue": {
                "name": "New Venue",
                "capacity": 50,
                "location_notes": "New notes",
                "virtual_url": "https://new.example.com",
            },
            "session_type": "Workshop",
            "level": "Intermediate",
            "status": "Proposed",
            "start_time": timezone.now().isoformat(),
            "end_time": (timezone.now() + timedelta(hours=2)).isoformat(),
            "max_attendees": 30,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Session.objects.filter(title="New Session").count(), 1)

    def test_retrieve_session(self):
        """Test retrieving a session detail."""
        url = reverse("sessions:session-detail", kwargs={"session_id": self.session.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.session.title)

    def test_update_session(self):
        """Test updating a session."""
        url = reverse("sessions:session-detail", kwargs={"session_id": self.session.id})
        data = {"title": "Updated Session Title"}
        # Ensure we have required nested data or the serializer might fail if it tries to validate them
        # Though partial=True is used in PATCH in the view.
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(self.session.title, "Updated Session Title")

    def test_delete_session(self):
        """Test deleting a session."""
        url = reverse("sessions:session-detail", kwargs={"session_id": self.session.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Session.objects.filter(id=self.session.id).count(), 0)

    def test_unauthenticated_list_sessions(self):
        """Test listing sessions as an unauthenticated user (should be allowed)."""
        self.client.logout()
        url = reverse("sessions:session-list", kwargs={"event_slug": self.event.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_create_session(self):
        """Test creating a session as an unauthenticated user (should be unauthorized)."""
        self.client.logout()
        url = reverse("sessions:session-list", kwargs={"event_slug": self.event.slug})
        data = {"title": "Unauthorized Session"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_member_create_session(self):
        """Test creating a session as a user who is not a member of the organization."""
        other_user = User.objects.create(
            username="otheruser", email="other@example.com", password="password123"
        )
        self.client.force_authenticate(user=other_user)
        url = reverse("sessions:session-list", kwargs={"event_slug": self.event.slug})
        data = {"title": "Non-member Session"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_serializer(self):
        """Test the session serializer directly."""
        serializer = SessionSerializer(self.session)
        self.assertEqual(serializer.data["title"], self.session.title)
        self.assertEqual(str(serializer.data["event"]), str(self.event.id))
