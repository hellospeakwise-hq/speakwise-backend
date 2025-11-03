"""users tests."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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


class RetrieveUpdateAuthenticatedUserViewTest(TestCase):
    """Test cases for RetrieveUpdateAuthenticatedUserView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("users:retrieve_update_authenticated_user")

    def test_get_authenticated_user(self):
        """Test retrieving authenticated user details."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)

    def test_get_unauthenticated(self):
        """Test retrieving user details without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_authenticated_user(self):
        """Test updating authenticated user details."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
        }

        response = self.client.put(self.url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data["first_name"])
        self.assertEqual(self.user.last_name, update_data["last_name"])

    def test_update_invalid_data(self):
        """Test updating with invalid data."""
        invalid_data = {
            "username": "",  # Username cannot be empty
            "first_name": "x" * 151,  # Too long (assuming max_length=150)
        }

        response = self.client.put(self.url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_unauthenticated(self):
        """Test updating user details without authentication."""
        self.client.force_authenticate(user=None)
        update_data = {"first_name": "Updated"}

        response = self.client.put(self.url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update(self):
        """Test partial update of user details."""
        original_last_name = self.user.last_name
        update_data = {"first_name": "NewFirst"}

        response = self.client.put(self.url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data["first_name"])
        # Last name should remain unchanged
        self.assertEqual(self.user.last_name, original_last_name)
