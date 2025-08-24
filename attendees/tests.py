"""attendees tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from attendees.models import AttendeeProfile, AttendeeSocialLinks
from attendees.serializers import (
    AttendeeProfileSerializer,
    AttendeeSocialLinksSerializer,
)


class AttendeeSerializerTestCase(TestCase):
    """Attendee serializer test case."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpassword"
        )

        self.attendee = AttendeeProfile.objects.create(
            first_name="John",
            last_name="Doe",
            email="attendee@mail.com",
            notification_preference="email",
            organization="TestOrg",
            user=self.user,
            is_verified=True,
        )
        self.social_link = AttendeeSocialLinks.objects.create(
            name="LinkedIn",
            link="https://www.linkedin.com/in/testuser",
            attendee=self.attendee,
        )
        self.serializer = AttendeeProfileSerializer(instance=self.attendee)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields."""
        data = self.serializer.data

        assert data.keys() == set(
            {
                "id",
                "first_name",
                "last_name",
                "email",
                "notification_preference",
                "organization",
                "is_verified",
                "user",
                "social_links",
            }
        )

    def test_field_content(self):
        """Test that the serializer contains the expected field content."""
        data = self.serializer.data

        assert data["first_name"] == self.attendee.first_name
        assert data["last_name"] == self.attendee.last_name
        assert data["email"] == self.attendee.email
        assert data["notification_preference"] == self.attendee.notification_preference
        assert data["organization"] == self.attendee.organization
        assert data["is_verified"] == self.attendee.is_verified
        assert data["user"] == self.user.id

    def test_social_links_serializer(self):
        """Test that the social links serializer works as expected."""
        serializer = AttendeeSocialLinksSerializer(instance=self.social_link)
        data = serializer.data

        assert set(data.keys()) == {"id", "name", "link"}
        assert data["name"] == self.social_link.name
        assert data["link"] == self.social_link.link
        assert data["id"] == self.social_link.id
