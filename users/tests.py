"""users tests."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

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


class TestPasswordReset(TestCase):
    """Test password reset views."""

    def setUp(self):
        """Test setup."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="testuser",
            email="test@mail.com",
            role=UserRole.objects.create(role=UserRoleChoices.ORGANIZER.value),
        )
        self.user.set_password("oldpassword123")
        self.user.save()
        # Ensure email backend is set to locmem for testing
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    def test_password_reset_request_success(self):
        """Test sending a password reset email with a valid email."""
        response = self.client.post(
            reverse("users:password_reset_request"),
            {"email": "test@mail.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["detail"], "Password reset email sent successfully."
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Password Reset Request")
        self.assertEqual(email.to, ["test@mail.com"])
        assert f"{settings.FRONTEND_URL}/reset-password/" in email.body

    def test_password_reset_request_invalid_email(self):
        """Test sending a password reset email with an invalid email."""
        response = self.client.post(
            reverse("users:password_reset_request"),
            {"email": "invalid@mail.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        assert "No user is associated with this email address." in str(response.data)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_success(self):
        """Test confirming a password reset with valid email and token."""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)

        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {
                "email": "test@mail.com",
                "token": token,
                "new_password": "newpassword123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Password reset successfully.")

        self.user.refresh_from_db()
        assert self.user.check_password("newpassword123")

    def test_password_reset_confirm_invalid_email(self):
        """Test confirming a password reset with an invalid email."""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)

        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {
                "email": "invalid@mail.com",
                "token": token,
                "new_password": "newpassword123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        assert "No user is associated with this email address." in str(response.data)

    def test_password_reset_confirm_invalid_token(self):
        """Test confirming a password reset with an invalid token."""
        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {
                "email": "test@mail.com",
                "token": "invalid-token",
                "new_password": "newpassword123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        assert "Invalid or expired token." in str(response.data)
