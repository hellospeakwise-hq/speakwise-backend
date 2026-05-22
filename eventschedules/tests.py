"""Events schedule API tests."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Event
from eventschedules.models import EventSchedule
from eventsessions.models import Session, SessionVenue, Track
from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
from users.models import User


class EventScheduleAPITestCase(APITestCase):
    """Test event schedule API."""

    def setUp(self):
        """Test setup."""
        self.user_admin = User.objects.create(
            username="admin", email="admin@test.com", password="password"
        )
        self.user_organizer = User.objects.create(
            username="organizer", email="organizer@test.com", password="password"
        )
        self.user_regular = User.objects.create(
            username="regular", email="regular@test.com", password="password"
        )

        self.organization = Organization.objects.create(
            name="Test Org", email="org@test.com"
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user_admin,
            role=OrganizationRole.ADMIN,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user_organizer,
            role=OrganizationRole.ORGANIZER,
        )

        self.event = Event.objects.create(
            title="Test Event",
            organizer=self.organization,
        )
        self.event2 = Event.objects.create(
            title="Other Event",
            organizer=self.organization,
        )

        self.session_track = Track.objects.create(name="Track")
        self.session_venue = SessionVenue.objects.create(name="Venue")

        self.session = Session.objects.create(
            event=self.event,
            track=self.session_track,
            venue=self.session_venue,
            title="Test Session",
        )
        self.session2 = Session.objects.create(
            event=self.event2,
            track=self.session_track,
            venue=self.session_venue,
            title="Other Session",
        )

        self.schedule = EventSchedule.objects.create(event=self.event)
        self.schedule.session.add(self.session)

    def test_list_event_schedules(self):
        """Test listing event schedules."""
        url = reverse("eventschedules:event-schedules-create")
        response = self.client.get(url, {"event_slug": self.event.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]["event"]), str(self.event.id))

    def test_create_event_schedule(self):
        """Test creating an event schedule."""
        url = reverse("eventschedules:event-schedules-create")
        data = {
            "event": self.event.id,
            "session": [self.session.id],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EventSchedule.objects.count(), 2)

    def test_retrieve_event_schedule(self):
        """Test retrieving an event schedule."""
        url = reverse("eventschedules:event-schedule-ret", args=[self.schedule.id])

        # Unauthorized
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Admin
        self.client.force_authenticate(user=self.user_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["event"]), str(self.event.id))

    def test_update_event_schedule(self):
        """Test updating an event schedule."""
        url = reverse("eventschedules:event-schedule-ret", args=[self.schedule.id])
        data = {
            "event": self.event.id,
        }

        self.client.force_authenticate(user=self.user_organizer)
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_event_schedule(self):
        """Test deleting an event schedule."""
        url = reverse("eventschedules:event-schedule-ret", args=[self.schedule.id])

        self.client.force_authenticate(user=self.user_regular)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user_admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(EventSchedule.objects.count(), 0)

    def test_serializer_validation(self):
        """Test serializer validation."""
        from eventschedules.serializers import EventScheduleSerializer

        data = {"event": self.event.id, "session": [self.session2.id]}
        serializer = EventScheduleSerializer(data=data, context={"event": self.event})
        self.assertTrue(serializer.is_valid())
