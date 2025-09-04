"""evetns tests."""

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from events.models import Country, Event, Location
from events.serializers import CountrySerializer, EventSerializer, LocationSerializer
from organizers.models import OrganizerProfile
from users.choices import UserRoleChoices
from users.models import User, UserRole


class TestEvent(TestCase):
    """test events models and serializers."""

    def setUp(self):
        """Test setup."""
        self.user = User.objects.create(
            username="testuser",
            email="test@mail.com",
            password="testpassword",
            role=UserRole.objects.create(role=UserRoleChoices.ORGANIZER.value),
        )
        self.country = Country.objects.create(name="Ghana")
        self.location = Location.objects.create(country=self.country)
        self.organizer = OrganizerProfile.objects.create(user_account=self.user)

        self.event = Event.objects.create(
            title="Test Event",
            description="This is a test event",
            location=self.location,
            organizer=self.organizer,
        )
        self.token = str(AccessToken.for_user(self.user))

    def test_event_model(self):
        """Test event model."""
        assert self.event.title == "Test Event"
        assert self.event.description == "This is a test event"
        assert self.event.location == self.location
        assert self.event.created_at == self.event.updated_at

    def test_event_serializer(self):
        """Test event serializer."""
        serializer = EventSerializer(instance=self.event)
        data = serializer.data

        assert data["title"] == "Test Event"
        assert data["description"] == "This is a test event"
        assert data["location"] == LocationSerializer(instance=self.location).data
        assert (
            data["location"].get("country")
            == CountrySerializer(instance=self.country).data
        )

    def test_event_create_api_view(self):
        """Test event create api view."""
        # Ensure all required fields are provided for event creation
        data = {"title": "Test Event 1", "description": "This is a test event"}
        # Use DRF test client format for auth header
        request = self.client.post(
            "/api/events/create/",
            data=data,
            headers={"authorization": f"Bearer {self.token}"},
        )

        assert request.status_code == 201
        assert request.data["title"] == "Test Event 1"
        assert request.data["description"] == "This is a test event"
