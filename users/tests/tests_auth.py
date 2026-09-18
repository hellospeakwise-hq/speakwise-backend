"""users tests."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import OrganizationProfile, SpeakerProfile
from users.models import User
from users.services.auth_services import LOGIN_LOCKOUT_MAX_ATTEMPTS


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


class UserLoginProfileDataTests(TestCase):
    """Tests that login responses detect and return the user's profiles."""

    def setUp(self):
        """Set up a client, login endpoint, and a user for testing."""
        cache.clear()
        self.client = APIClient()
        self.login_url = reverse("users:login")
        self.user = User.objects.create(
            username="profile_login_user",
            email="profile_login@example.com",
            is_email_verified=True,
        )
        self.user.set_password("password123")
        self.user.save()

    def _login(self) -> dict:
        """POST valid credentials and return the response data."""
        response = self.client.post(
            self.login_url,
            {"email": "profile_login@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_login_returns_speaker_profile_data(self):
        """A user's speaker profile is returned in the login response."""
        SpeakerProfile.objects.create(user_account=self.user, organization="Acme")
        profiles = self._login()["profile"]
        self.assertIsNotNone(profiles["speaker_profile"])
        self.assertEqual(
            str(profiles["speaker_profile"]["user_account"]), str(self.user.id)
        )
        self.assertEqual(profiles["speaker_profile"]["organization"], "Acme")
        self.assertNotIn("organization_profile", profiles)

    def test_login_returns_organization_profile_data(self):
        """An owned organization profile is returned in the login response."""
        OrganizationProfile.objects.create(name="Acme Org", owner=self.user)
        profiles = self._login()["profile"]
        self.assertIsNotNone(profiles["organization_profile"])
        self.assertEqual(profiles["organization_profile"]["name"], "Acme Org")
        # A user can have one and only one profile, so no speaker profile
        # coexists with the organization profile.
        self.assertNotIn("speaker_profile", profiles)

    def test_login_returns_no_profiles_when_user_has_none(self):
        """A user without any profiles gets an empty profiles object."""
        user = User.objects.create(
            username="bareuser",
            email="bare@example.com",
            is_email_verified=True,
        )
        user.set_password("password123")
        user.save()

        response = self.client.post(
            self.login_url,
            {"email": "bare@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profiles = response.data["profile"]
        self.assertEqual(profiles, {})


class TestPasswordReset(TestCase):
    """Test password reset views."""

    def setUp(self):
        """Test setup."""
        cache.clear()
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
        assert f"{settings.FRONTEND_URL}/reset-password?" in email.body

    def test_password_reset_request_unknown_email_is_non_committal(self):
        """Unknown emails get the same success response, but no email goes out."""
        response = self.client.post(
            reverse("users:password_reset_request"),
            {"email": "invalid@mail.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["detail"], "Password reset email sent successfully."
        )
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

    def test_password_reset_confirm_rejects_weak_password(self):
        """Common passwords are rejected by the project's password policy."""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)

        response = self.client.post(
            reverse("users:password_reset_confirm"),
            {
                "email": "test@mail.com",
                "token": token,
                "new_password": "password",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("password"))


class TestUserRegistrationPasswordPolicy(TestCase):
    """Registration enforces the project password policy."""

    def setUp(self):
        """Set up the registration endpoint."""
        cache.clear()
        self.client = APIClient()
        self.register_url = reverse("users:register")

    def _register(self, password: str):
        """POST a registration with the given password."""
        return self.client.post(
            self.register_url,
            {
                "email": "pw@example.com",
                "username": "pwuser",
                "password": password,
            },
            format="json",
        )

    def test_registration_rejects_weak_password(self):
        """A common password is rejected with a 400."""
        response = self._register("password")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_numeric_password(self):
        """A purely numeric password is rejected with a 400."""
        response = self._register("12345678")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="pw@example.com").exists())

    def test_registration_accepts_strong_password(self):
        """A strong password still registers successfully."""
        response = self._register("StrongPass123!")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="pw@example.com").exists())


class TestUserLoginFailure(TestCase):
    """Failed logins return a generic message and lock the account."""

    def setUp(self):
        """Set up a user and the login endpoint."""
        cache.clear()
        self.client = APIClient()
        self.login_url = reverse("users:login")
        self.user = User.objects.create(username="loginuser", email="login@example.com")
        self.user.set_password("password123")
        self.user.save()

    def _login(self, email: str, password: str):
        """POST login credentials and return the response."""
        return self.client.post(
            self.login_url,
            {"email": email, "password": password},
            format="json",
        )

    def test_wrong_password_returns_generic_message(self):
        """A bad password returns a generic 400 instead of a redirect."""
        response = self._login("login@example.com", "wrongpass")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unable to log in", str(response.data))

    def test_unknown_email_returns_generic_message(self):
        """An unknown email is indistinguishable from a wrong password."""
        response = self._login("nobody@example.com", "whatever")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unable to log in", str(response.data))

    def test_login_is_locked_after_max_failed_attempts(self):
        """Enough failed attempts lock the account even for the right password."""
        for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
            self._login("login@example.com", "wrongpass")
        response = self._login("login@example.com", "password123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestUsersListView(TestCase):
    """The user list is restricted to staff and paginated."""

    def setUp(self):
        """Set up a normal user, a staff user, and the list endpoint."""
        cache.clear()
        self.client = APIClient()
        self.url = reverse("users:user-list")
        self.normal = User.objects.create(username="normal", email="normal@example.com")
        self.staff = User.objects.create(
            username="staff", email="staff@example.com", is_staff=True
        )

    def test_unauthenticated_user_is_rejected(self):
        """Anonymous requests are rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_non_staff_user_is_forbidden(self):
        """Regular authenticated users cannot list the user table."""
        self.client.force_authenticate(user=self.normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_gets_paginated_results(self):
        """Staff can list users and receive the paginated envelope."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("normal", usernames)
        self.assertIn("staff", usernames)


class RetrieveUpdateAuthenticatedUserViewTest(TestCase):
    """Test cases for RetrieveUpdateAuthenticatedUserView."""

    def setUp(self):
        """Set up test user and client."""
        cache.clear()
        mail.outbox.clear()
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        self.client = APIClient()
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            is_email_verified=True,
        )
        self.user.set_password("testpass123")
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("users:retrieve_update_authenticated_user")

    def test_get_authenticated_user(self):
        """Test retrieving authenticated user details."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure expected fields from UserSerializer are present
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)
        self.assertEqual(response.data.get("nationality"), self.user.nationality)

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
            "nationality": "Uganda",
        }
        response = self.client.patch(self.url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data["first_name"])
        self.assertEqual(self.user.last_name, update_data["last_name"])
        self.assertEqual(self.user.nationality, update_data["nationality"])

    def test_email_change_requires_otp_reverification(self):
        """Changing the email resets verification and OTPs the new address."""
        data = {"email": "new@example.com", "password": "newpass123"}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertFalse(self.user.is_email_verified)
        self.assertEqual(response.data["is_email_verified"], False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["new@example.com"])

    def test_update_without_email_change_keeps_verification(self):
        """Updating other fields does not trip re-verification."""
        response = self.client.patch(
            self.url, {"first_name": "Updated", "nationality": "Uganda"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertEqual(len(mail.outbox), 0)

    def test_update_invalid_data(self):
        """Test updating user with invalid data."""
        # username is required and must be non-empty; send invalid username
        invalid_data = {"username": ""}
        response = self.client.patch(self.url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_unauthenticated(self):
        """Test updating user details without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.patch(
            self.url, {"user": {"first_name": "X"}}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_with_speaker_profile(self):
        """Test updating user details along with speaker profile."""
        self.client.force_authenticate(self.user)
        sp = SpeakerProfile.objects.filter(user_account=self.user).first()
        payload = {
            "first_name": "Speaker",
            "last_name": "One",
            "speaker": {
                "id": sp.id if sp else None,
                "organization": "Acme Org",
                "short_bio": "Hello world",
                "user_account": self.user.id,
            },
        }

        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Speaker")
        self.assertEqual(self.user.last_name, "One")
