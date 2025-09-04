"""users tests."""

from django.test import TestCase

from users.choices import UserRoleChoices
from users.models import User, UserRole


class TestUserModel(TestCase):
    """test user model."""

    def setUp(self):
        """Test setup."""
        self.user = User.objects.create(
            username="testuser",
            email="test@mail.com",
            password="PASSWORD",
            role=UserRole.objects.create(role=UserRoleChoices.ORGANIZER.value),
        )

    def test_user_role_methods(self):
        """Test is_attendance."""
        assert self.user.is_attendance() is False
        assert self.user.is_speaker() is False
        assert self.user.is_admin() is False
        assert self.user.is_organizer_or_admin() is True
        assert self.user.is_organizer() is True

    def test_user_creation(self):
        """Test user creation."""
        assert self.user.username == "testuser"
        assert self.user.email == "test@mail.com"
        assert self.user.role.role == UserRoleChoices.ORGANIZER.value
        assert self.user.check_user_role(UserRoleChoices.ORGANIZER.value) is True

    def test_user_role_creation(self):
        """Test user role creation."""
        assert self.user.role.role == UserRoleChoices.ORGANIZER.value
        assert self.user.role.role != UserRoleChoices.ADMIN.value
        assert self.user.role.role != UserRoleChoices.ATTENDEE.value
        assert self.user.role.role != UserRoleChoices.SPEAKER.value
