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
            "is_active": True,
            "organizer": self.organization,
        }

        self.event = Event.objects.create(**self.event_data)

    def test_get_event_list(self):
        """Test retrieving the event list."""
        url = reverse("v1:events:event-list-create")
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
        url = reverse("v1:events:event-list-create")
        new_event_data = {
            "title": "New Test Event",
            "short_description": "This is another test event.",
            "website": "https://newevent.com",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, new_event_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], new_event_data["title"])
        self.assertEqual(str(response.data["organizer"]), str(self.organization.id))

    def test_update_event_unauthorized(self):
        """Test that a user from another organization cannot update this event."""
        other_user = User.objects.create(
            username="otheruser",
            email="otheruser@mail.com",
            password="testpassword",
        )
        other_org = Organization.objects.create(
            name="Other Organization",
            email="other@org.com",
            created_by=other_user,
        )
        OrganizationMembership.objects.create(
            user=other_user,
            organization=other_org,
            role=OrganizationRole.ADMIN.value,
        )

        url = reverse("v1:events:event-detail", kwargs={"slug": self.event.slug})
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(url, {"title": "Hacked Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_event_unauthorized(self):
        """Test that a user from another organization cannot delete this event."""
        other_user = User.objects.create(
            username="otheruser2",
            email="otheruser2@mail.com",
            password="testpassword",
        )
        other_org = Organization.objects.create(
            name="Other Organization 2",
            email="other2@org.com",
            created_by=other_user,
        )
        OrganizationMembership.objects.create(
            user=other_user,
            organization=other_org,
            role=OrganizationRole.ADMIN.value,
        )

        url = reverse("v1:events:event-detail", kwargs={"slug": self.event.slug})
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())
