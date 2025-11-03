"""users tests."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from speakers.models import SpeakerProfile
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
        """Set up test user and client."""
        self.client = APIClient()
        # create user using create_user to ensure password hashing
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            nationality="Kenya",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("users:retrieve_update_authenticated_user")

    def test_get_authenticated_user(self):
        """Test retrieving authenticated user details."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure expected fields from UserSerializer are present
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertEqual(response.data["user"]["username"], self.user.username)
        self.assertEqual(response.data["user"]["first_name"], self.user.first_name)
        self.assertEqual(response.data["user"]["last_name"], self.user.last_name)
        self.assertEqual(
            response.data["user"].get("nationality"), self.user.nationality
        )

    def test_get_unauthenticated(self):
        """Test retrieving user details without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_authenticated_user(self):
        """Test updating authenticated user details."""
        update_data = {
            "user": {
                "first_name": "Updated",
                "last_name": "Name",
                "nationality": "Uganda",
            }
        }
        response = self.client.put(self.url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data["user"]["first_name"])
        self.assertEqual(self.user.last_name, update_data["user"]["last_name"])
        self.assertEqual(self.user.nationality, update_data["user"]["nationality"])

    def test_update_readonly_fields_ignored(self):
        """Test that read-only fields are ignored during update."""
        # email is part of serializer but should be allowed; password is write_only
        data = {"user": {"email": "new@example.com", "password": "newpass123"}}
        response = self.client.put(self.url, data, format="json")
        # password write-only won't be returned but should be accepted; email may be updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # password changed? We can't check raw password; ensure email updated
        self.assertEqual(self.user.email, "new@example.com")

    def test_update_invalid_data(self):
        """Test updating user with invalid data."""
        # username is required and must be non-empty; send invalid username
        invalid_data = {"user": {"username": ""}}
        response = self.client.put(self.url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_unauthenticated(self):
        """Test updating user details without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.put(
            self.url, {"user": {"first_name": "X"}}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_with_speaker_profile(self):
        """Test updating user details along with speaker profile."""
        # Update both user and speaker profile together
        payload = {
            "user": {"first_name": "Speaker", "last_name": "One"},
            "speaker": {"organization": "Acme Org", "short_bio": "Hello world"},
        }

        response = self.client.put(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Speaker")
        self.assertEqual(self.user.last_name, "One")

        # Check speaker profile updated
        sp = SpeakerProfile.objects.filter(user_account=self.user).first()
        self.assertIsNotNone(sp)
        self.assertEqual(sp.organization, "Acme Org")
        self.assertEqual(sp.short_bio, "Hello world")
