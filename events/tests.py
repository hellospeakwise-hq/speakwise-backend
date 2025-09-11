"""evetns tests."""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from events.filters import EventFilter
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
        assert abs((self.event.created_at - self.event.updated_at).total_seconds()) < 1

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
            "/api/events/",
            data=data,
            headers={"authorization": f"Bearer {self.token}"},
        )

        assert request.status_code == 201
        assert request.data["title"] == "Test Event 1"
        assert request.data["description"] == "This is a test event"


class TestEventFilter(TestCase):
    """Test EventFilter functionality."""

    def setUp(self):
        """Set up test data for filtering."""
        # Create users and organizers
        self.organizer1_user = User.objects.create(
            username="john_organizer",
            email="john@mail.com",
            password="testpassword",
            role=UserRole.objects.create(role=UserRoleChoices.ORGANIZER.value),
        )
        self.organizer1 = OrganizerProfile.objects.create(
            user_account=self.organizer1_user
        )

        self.organizer2_user = User.objects.create(
            username="jane_organizer",
            email="jane@mail.com",
            password="testpassword",
            role=UserRole.objects.create(role=UserRoleChoices.ORGANIZER.value),
        )
        self.organizer2 = OrganizerProfile.objects.create(
            user_account=self.organizer2_user
        )

        # Create countries and locations
        self.usa = Country.objects.create(name="United States", code="US")
        self.ghana = Country.objects.create(name="Ghana", code="GH")

        self.auditorium_usa = Location.objects.create(
            venue="Grand Auditorium", city="New York", country=self.usa
        )
        self.conference_center_usa = Location.objects.create(
            venue="Tech Conference Center", city="San Francisco", country=self.usa
        )
        self.auditorium_ghana = Location.objects.create(
            venue="National Theater", city="Accra", country=self.ghana
        )

        # Create test events
        self.conference_event = Event.objects.create(
            title="Tech Conference 2024",
            description="Annual tech conference",
            organizer=self.organizer1,
            location=self.auditorium_usa,
        )
        self.workshop_event = Event.objects.create(
            title="Python Workshop",
            description="Learn Python programming",
            organizer=self.organizer2,
            location=self.conference_center_usa,
        )
        self.meetup_event = Event.objects.create(
            title="Developer Meetup",
            description="Local developer meetup",
            organizer=self.organizer1,
            location=self.auditorium_ghana,
        )

    def test_title_filter_exact_match(self):
        """Test filtering events by exact title match."""
        filter_set = EventFilter(data={"title": "Tech Conference 2024"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.conference_event in filtered_queryset

    def test_title_filter_partial_match(self):
        """Test filtering events by partial title match (case insensitive)."""
        filter_set = EventFilter(data={"title": "conference"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.conference_event in filtered_queryset

    def test_title_filter_case_insensitive(self):
        """Test that title filter is case insensitive."""
        filter_set = EventFilter(data={"title": "PYTHON"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.workshop_event in filtered_queryset

    def test_title_filter_no_match(self):
        """Test title filter with no matches."""
        filter_set = EventFilter(data={"title": "nonexistent"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 0

    def test_organizer_filter_exact_username(self):
        """Test filtering events by organizer username."""
        filter_set = EventFilter(data={"organizer": "john_organizer"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 2
        assert self.conference_event in filtered_queryset
        assert self.meetup_event in filtered_queryset

    def test_organizer_filter_partial_username(self):
        """Test filtering events by partial organizer username."""
        filter_set = EventFilter(data={"organizer": "jane"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.workshop_event in filtered_queryset

    def test_organizer_filter_case_insensitive(self):
        """Test that organizer filter is case insensitive."""
        filter_set = EventFilter(data={"organizer": "JOHN"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 2
        assert self.conference_event in filtered_queryset
        assert self.meetup_event in filtered_queryset

    def test_country_filter_exact_name(self):
        """Test filtering events by country name."""
        filter_set = EventFilter(data={"country": "United States"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 2
        assert self.conference_event in filtered_queryset
        assert self.workshop_event in filtered_queryset

    def test_country_filter_partial_name(self):
        """Test filtering events by partial country name."""
        filter_set = EventFilter(data={"country": "Ghana"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.meetup_event in filtered_queryset

    def test_country_filter_case_insensitive(self):
        """Test that country filter is case insensitive."""
        filter_set = EventFilter(data={"country": "ghana"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.meetup_event in filtered_queryset

    def test_venue_filter_exact_name(self):
        """Test filtering events by venue name."""
        filter_set = EventFilter(data={"venue": "Grand Auditorium"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.conference_event in filtered_queryset

    def test_venue_filter_partial_name(self):
        """Test filtering events by partial venue name."""
        filter_set = EventFilter(data={"venue": "auditorium"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.conference_event in filtered_queryset

    def test_venue_filter_case_insensitive(self):
        """Test that venue filter is case insensitive."""
        filter_set = EventFilter(data={"venue": "THEATER"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.meetup_event in filtered_queryset

    def test_multiple_filters_combined(self):
        """Test combining multiple filters."""
        filter_set = EventFilter(data={"organizer": "john", "country": "United States"})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 1
        assert self.conference_event in filtered_queryset

    def test_no_filters_returns_all_events(self):
        """Test that no filters returns all events."""
        filter_set = EventFilter(data={})
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 3

    def test_invalid_filter_returns_empty_queryset(self):
        """Test that invalid filter values return empty queryset."""
        filter_set = EventFilter(
            data={
                "organizer": "nonexistent_user",
                "country": "nonexistent_country",
                "venue": "nonexistent_venue",
                "title": "nonexistent_title",
            }
        )
        filtered_queryset = filter_set.qs

        assert filtered_queryset.count() == 0


class TestEventFilterAPIView(APITestCase):
    """Test EventFilter integration with API views."""

    def setUp(self):
        """Set up test data for API testing."""
        # Create user and organizer for authentication
        self.user = User.objects.create(
            username="api_user",
            email="api@mail.com",
            password="testpassword",
            role=UserRole.objects.create(role=UserRoleChoices.ORGANIZER.value),
        )
        self.organizer = OrganizerProfile.objects.create(user_account=self.user)

        # Create test data similar to unit tests
        self.usa = Country.objects.create(name="United States", code="US")
        self.location = Location.objects.create(
            venue="API Test Venue", city="Test City", country=self.usa
        )

        self.test_event = Event.objects.create(
            title="API Test Conference",
            description="Test event for API",
            organizer=self.organizer,
            location=self.location,
        )

    def test_api_title_filter(self):
        """Test title filtering through API endpoint."""
        url = "/api/events/"
        response = self.client.get(url, {"title": "API Test"})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["title"] == "API Test Conference"

    def test_api_organizer_filter(self):
        """Test organizer filtering through API endpoint."""
        url = "/api/events/"
        response = self.client.get(url, {"organizer": "api_user"})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["organizer"] == self.organizer.id

    def test_api_country_filter(self):
        """Test country filtering through API endpoint."""
        url = "/api/events/"
        response = self.client.get(url, {"country": "United States"})

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_api_venue_filter(self):
        """Test venue filtering through API endpoint."""
        url = "/api/events/"
        response = self.client.get(url, {"venue": "API Test Venue"})

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_api_no_results_filter(self):
        """Test API filter that returns no results."""
        url = "/api/events/"
        response = self.client.get(url, {"title": "nonexistent"})

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_api_multiple_filters(self):
        """Test combining multiple filters via API."""
        url = "/api/events/"
        response = self.client.get(
            url, {"title": "API", "organizer": "api_user", "country": "United States"}
        )

        assert response.status_code == 200
        assert len(response.data) == 1
