"""evetns tests."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event
from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
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
        self.organization = Organization.objects.create(
            name="Test Organization",
            description="This is a test organization.",
            created_by=self.user,
        )
        self.membership = OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization,
            role=OrganizationRole.ADMIN.value,
        )
        self.event_data = {
            "title": "Test Event",
            "short_description": "This is a test event.",
            "website": "https://testevent.com",
        }

        self.event = Event.objects.create(**self.event_data)

    def test_get_event_list(self):
        """Test retrieving the event list."""
        url = reverse("events:event-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_event(self):
        """Test creating a new event."""
        url = reverse("events:event-list-create")
        new_event_data = {
            "title": "New Test Event",
            "short_description": "This is another test event.",
            "website": "https://newevent.com",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, new_event_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], new_event_data["title"])
