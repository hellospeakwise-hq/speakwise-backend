"""OAuth tests."""

from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import OrganizationProfile, SpeakerProfile
from users.models import OAuthExchangeCode, User

FRONTEND_URL = "http://test-frontend"


@override_settings(FRONTEND_URL=FRONTEND_URL)
class OAuthTests(TestCase):
    """Test OAuth flows."""

    def setUp(self):
        """Test setup."""
        cache.clear()
        self.client = APIClient()
        self.github_login_url = reverse("users:github-login")
        self.github_callback_url = reverse("users:github-callback")
        self.google_login_url = reverse("users:google-login")
        self.google_callback_url = reverse("users:google-callback")
        self.exchange_url = reverse("users:oauth-token-exchange")

    def _exchange_code(self, response) -> str:
        """Extract the one-time code from a callback redirect URL."""
        params = parse_qs(urlparse(response.url).query)
        self.assertIn("code", params)
        return params["code"][0]

    def _exchange(self, code: str):
        """POST the exchange endpoint with the given code."""
        return self.client.post(self.exchange_url, {"code": code}, format="json")

    @patch("users.views.oauth_views.get_github_session")
    def test_github_login_redirect(self, mock_get_session):
        """Test GitHub login redirection."""
        mock_github = mock_get_session.return_value
        mock_github.authorization_url.return_value = (
            "https://github.com/login/oauth/authorize?state=test",
            "test_state",
        )
        response = self.client.get(self.github_login_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response.url, "https://github.com/login/oauth/authorize?state=test"
        )
        self.assertEqual(self.client.session["oauth_state"], "test_state")

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_success(self, mock_get_session):
        """The callback redirects with a code, not tokens."""
        mock_github = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "test@github.com", "login": "githubuser"},
        ]
        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertNotIn("access", response.url)
        self.assertNotIn("refresh", response.url)
        self.assertNotIn("user=", response.url)

        exchange = self._exchange(self._exchange_code(response))
        self.assertEqual(exchange.status_code, status.HTTP_200_OK)
        self.assertEqual(exchange.data["email"], "test@github.com")
        self.assertIn("access", exchange.data)
        self.assertIn("refresh", exchange.data)

        user = User.objects.get(email="test@github.com")
        self.assertEqual(user.username, "githubuser")
        self.assertFalse(SpeakerProfile.objects.filter(user_account=user).exists())

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_invalid_state(self, mock_get_session):
        """Test GitHub callback with invalid state."""
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "wrong_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid state parameter")

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_state_is_consumed(self, mock_get_session):
        """A used state cannot be replayed to mint more codes."""
        mock_github = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "state@example.com", "login": "stateuser"},
        ]

        self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertNotIn("oauth_state", self.client.session)

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_missing_email_is_rejected(self, mock_get_session):
        """A provider response without an email is rejected with a clear error."""
        mock_github = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"login": "noemail"},  # user info without email
            [],  # emails list empty
        ]

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Email not found from GitHub")

    @patch("users.views.oauth_views.get_google_session")
    def test_google_login_redirect(self, mock_get_session):
        """Test Google login redirection."""
        mock_google = mock_get_session.return_value
        mock_google.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/v2/auth?state=test",
            "test_state",
        )
        response = self.client.get(self.google_login_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response.url, "https://accounts.google.com/o/oauth2/v2/auth?state=test"
        )
        self.assertEqual(self.client.session["oauth_state"], "test_state")

    @patch("users.views.oauth_views.get_google_session")
    def test_google_callback_success(self, mock_get_session):
        """Test Google callback success with a normalized username."""
        mock_google = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_google.fetch_token.return_value = {"access_token": "token"}
        mock_google.get.return_value.json.return_value = {
            "email": "test@google.com",
            "name": "Google User",
        }

        response = self.client.get(
            self.google_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        exchange = self._exchange(self._exchange_code(response))
        self.assertEqual(exchange.status_code, status.HTTP_200_OK)
        user = User.objects.get(email="test@google.com")
        self.assertEqual(user.username, "google-user")


@override_settings(FRONTEND_URL=FRONTEND_URL)
class OAuthCodeExchangeTests(TestCase):
    """The one-time exchange code is single-use and short-lived."""

    def setUp(self):
        """Set up the exchange endpoint and a user."""
        cache.clear()
        self.client = APIClient()
        self.exchange_url = reverse("users:oauth-token-exchange")
        self.user = User.objects.create(
            email="exchange@example.com", username="exchangeuser"
        )

    def _issue_code(self) -> str:
        """Create and return a plaintext exchange code for the test user."""
        from users.services.oauth_services import create_exchange_code

        return create_exchange_code(self.user)

    def _exchange(self, code: str):
        """POST the exchange endpoint with the given code."""
        return self.client.post(self.exchange_url, {"code": code}, format="json")

    def test_valid_code_exchanges_for_tokens(self):
        """A valid code returns the access/refresh/user payload."""
        response = self._exchange(self._issue_code())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "exchange@example.com")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_code_is_single_use(self):
        """A consumed code cannot be exchanged twice."""
        code = self._issue_code()
        self.assertEqual(self._exchange(code).status_code, status.HTTP_200_OK)
        second = self._exchange(code)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_code_is_rejected(self):
        """A fabricated code is rejected with a generic 400."""
        response = self._exchange("not-a-real-code")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired", str(response.data))

    def test_expired_code_is_rejected(self):
        """An expired code is rejected and not consumed."""
        code = self._issue_code()
        OAuthExchangeCode.objects.update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        response = self._exchange(code)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        code_row = OAuthExchangeCode.objects.get()
        self.assertFalse(code_row.is_used)


@override_settings(FRONTEND_URL=FRONTEND_URL)
class OAuthProfileDataTests(TestCase):
    """Test that OAuth callbacks detect and return the user's profiles."""

    def setUp(self):
        """Set up a client and callback URLs."""
        cache.clear()
        self.client = APIClient()
        self.github_callback_url = reverse("users:github-callback")
        self.google_callback_url = reverse("users:google-callback")
        self.exchange_url = reverse("users:oauth-token-exchange")

    def _exchange_code(self, response) -> str:
        """Extract the one-time code from a callback redirect URL."""
        params = parse_qs(urlparse(response.url).query)
        return params["code"][0]

    def _respond_to_callback(self, callback_url: str):
        """Set up session state and mock patches for a callback."""
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        return self.client.get(callback_url, {"code": "code", "state": "test_state"})

    def _exchange(self, code: str):
        """POST the exchange endpoint with the given code."""
        return self.client.post(self.exchange_url, {"code": code}, format="json")

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_returns_profiles_for_new_user(self, mock_get_session):
        """A newly created OAuth user gets their profiles reported."""
        mock_github = mock_get_session.return_value
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_profile@example.com", "login": "ghprofile"}
        ]

        response = self._respond_to_callback(self.github_callback_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        exchange = self._exchange(self._exchange_code(response))
        # Signup does not auto-create a profile; a new user has neither type.
        self.assertEqual(exchange.data["profile"], {})

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_marks_new_user_email_verified(self, mock_get_session):
        """A user created via GitHub OAuth skips OTP verification."""
        mock_github = mock_get_session.return_value
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_verified@example.com", "login": "ghverified"}
        ]

        response = self._respond_to_callback(self.github_callback_url)
        exchange = self._exchange(self._exchange_code(response))
        self.assertEqual(exchange.status_code, status.HTTP_200_OK)
        user = User.objects.get(email="gh_verified@example.com")
        self.assertTrue(user.is_email_verified)
        self.assertTrue(exchange.data["is_email_verified"])

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_verifies_existing_email_user(self, mock_get_session):
        """A returning OAuth login verifies an email/password account's email."""
        user = User.objects.create(
            email="gh_existing@example.com",
            username="ghexisting",
            is_email_verified=False,
        )
        mock_github = mock_get_session.return_value
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_existing@example.com", "login": "ghexisting"}
        ]

        response = self._respond_to_callback(self.github_callback_url)
        exchange = self._exchange(self._exchange_code(response))
        self.assertEqual(exchange.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_returns_existing_speaker_profile(self, mock_get_session):
        """A returning OAuth user with a speaker profile gets it reported."""
        user = User.objects.create(
            email="gh_existing@example.com", username="ghexisting"
        )
        SpeakerProfile.objects.create(user_account=user, organization="Acme")

        mock_github = mock_get_session.return_value
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_existing@example.com", "login": "ghexisting"}
        ]

        response = self._respond_to_callback(self.github_callback_url)
        exchange = self._exchange(self._exchange_code(response))
        profiles = exchange.data["profile"]
        self.assertIsNotNone(profiles["speaker_profile"])
        self.assertEqual(profiles["speaker_profile"]["organization"], "Acme")
        self.assertNotIn("organization_profile", profiles)

    @patch("users.views.oauth_views.get_google_session")
    def test_google_callback_returns_existing_organization_profile(
        self, mock_get_session
    ):
        """A returning OAuth user with an organization gets it reported."""
        user = User.objects.create(
            email="gl_existing@example.com", username="glexisting"
        )
        OrganizationProfile.objects.create(name="Acme Org", owner=user)

        mock_google = mock_get_session.return_value
        mock_google.fetch_token.return_value = {"access_token": "token"}
        mock_google.get.return_value.json.return_value = {
            "email": "gl_existing@example.com",
            "name": "gl_existing",
        }

        response = self._respond_to_callback(self.google_callback_url)
        exchange = self._exchange(self._exchange_code(response))
        profiles = exchange.data["profile"]
        self.assertIsNotNone(profiles["organization_profile"])
        self.assertEqual(profiles["organization_profile"]["name"], "Acme Org")
        self.assertNotIn("speaker_profile", profiles)

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_username_collision_gets_unique_suffix(
        self, mock_get_session
    ):
        """A taken provider username is disambiguated instead of erroring."""
        User.objects.create(email="taken@example.com", username="githubuser")
        mock_github = mock_get_session.return_value
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_second@example.com", "login": "githubuser"}
        ]

        response = self._respond_to_callback(self.github_callback_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        user = User.objects.get(email="gh_second@example.com")
        self.assertEqual(user.username, "githubuser2")
