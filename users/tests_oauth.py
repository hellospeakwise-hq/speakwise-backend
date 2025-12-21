"""OAuth tests."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from speakers.models import SpeakerProfile
from users.models import User


class OAuthTests(TestCase):
    """Test OAuth flows."""

    def setUp(self):
        """Test setup."""
        self.client = APIClient()
        self.github_login_url = reverse("users:github-login")
        self.github_callback_url = reverse("users:github-callback")
        self.google_login_url = reverse("users:google-login")
        self.google_callback_url = reverse("users:google-callback")

    @patch("users.oauth_views.get_github_session")
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

    @patch("users.oauth_views.get_github_session")
    def test_github_callback_success(self, mock_get_session):
        """Test GitHub callback success."""
        mock_github = mock_get_session.return_value
        # Mock session state
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()

        # Mock GitHub responses
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "test@github.com", "login": "githubuser"},  # user info
        ]

        response = self.client.get(
            self.github_callback_url,
            {"code": "code", "state": "test_state", "role": "speaker"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], "test@github.com")

        # Verify user created
        user = User.objects.get(email="test@github.com")
        self.assertEqual(user.username, "githubuser")

        # Verify profile created
        self.assertTrue(SpeakerProfile.objects.filter(user_account=user).exists())

    @patch("users.oauth_views.get_github_session")
    def test_github_callback_invalid_state(self, mock_get_session):
        """Test GitHub callback with invalid state."""
        # No need to mock github here as it should fail before using it,
        # but the view calls get_github_session() so we mock it.
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "wrong_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid state parameter")

    @patch("users.oauth_views.get_google_session")
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

    @patch("users.oauth_views.get_google_session")
    def test_google_callback_success(self, mock_get_session):
        """Test Google callback success."""
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], "test@google.com")

        user = User.objects.get(email="test@google.com")
        self.assertEqual(user.username, "Google User")
