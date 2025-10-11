"""users tests."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from users.filters import UserFilter
from users.models import User


class TestUserModel(TestCase):
    """test user model."""

    def setUp(self):
        """Test setup."""
        self.user = User.objects.create(
            username="testuser",
            email="test@mail.com",
            password="PASSWORD",
        )

    def test_user_creation(self):
        """Test user creation."""
        assert self.user.username == "testuser"
        assert self.user.email == "test@mail.com"


class TestPasswordReset(TestCase):
    """Test password reset views."""

    def setUp(self):
        """Test setup."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="testuser",
            email="test@mail.com",
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
        self.assertEqual(email.subject, "Password Reset Request - SpeakWise")
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


class UserFilterTest(TestCase):
    """Test cases for UserFilter."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create(
            username="johndoe", email="john@example.com", password="password123"
        )
        self.user2 = User.objects.create(
            username="janedoe", email="jane@example.com", password="password123"
        )
        self.user3 = User.objects.create(
            username="bobsmith", email="bob@test.com", password="password123"
        )
        self.queryset = User.objects.all()

    def test_username_filter(self):
        """Test filtering users by username."""
        filterset = UserFilter({"username": "doe"}, queryset=self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertNotIn(self.user3, filterset.qs)

    def test_email_filter(self):
        """Test filtering users by email."""
        filterset = UserFilter({"email": "example"}, queryset=self.queryset)
        self.assertEqual(filterset.qs.count(), 2)
        self.assertNotIn(self.user3, filterset.qs)

    def test_filter_users_method(self):
        """Test the filter_users method that searches both fields."""
        filter_instance = UserFilter()

        # Test filtering by username
        result = filter_instance.filter_users(self.queryset, "username", "jane")
        self.assertEqual(result.count(), 1)

        # Test filtering by email
        result = filter_instance.filter_users(self.queryset, "email", "test")
        self.assertEqual(result.count(), 1)

        # Test filtering with no results
        result = filter_instance.filter_users(self.queryset, "username", "nonexistent")
        self.assertEqual(result.count(), 0)

        # Test filtering with empty value
        result = filter_instance.filter_users(self.queryset, "username", "")
        self.assertEqual(result.count(), 3)  # Returns all users
