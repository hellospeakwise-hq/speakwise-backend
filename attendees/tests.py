"""attendees tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from attendees.models import AttendeeProfile, AttendeeSocialLinks
from attendees.serializers import (
    AttendeeProfileSerializer,
    AttendeeSocialLinksSerializer,
)
from users.choices import UserRoleChoices
from users.models import UserRole


class AttendeeSerializerTestCase(TestCase):
    """Attendee serializer test case."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create(
            username="testuser",
            password="testpassword",
            email="test@mail.com",
            role=UserRole.objects.create(role=UserRoleChoices.ATTENDEE.value),
        )

        self.attendee = AttendeeProfile.objects.create(
            notification_preference="email",
            organization="TestOrg",
            user_account=self.user,
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

        assert data.keys() == (
            {
                "id",
                "notification_preference",
                "organization",
                "is_verified",
                "user_account",
                "social_links",
            }
        )

    def test_field_content(self):
        """Test that the serializer contains the expected field content."""
        data = self.serializer.data

        assert data["notification_preference"] == self.attendee.notification_preference
        assert data["organization"] == self.attendee.organization
        assert data["is_verified"] == self.attendee.is_verified
        assert data["user_account"] == self.user.id

    def test_social_links_serializer(self):
        """Test that the social links serializer works as expected."""
        serializer = AttendeeSocialLinksSerializer(instance=self.social_link)
        data = serializer.data

        assert set(data.keys()) == {"id", "name", "link"}
        assert data["name"] == self.social_link.name
        assert data["link"] == self.social_link.link
        assert data["id"] == self.social_link.id
