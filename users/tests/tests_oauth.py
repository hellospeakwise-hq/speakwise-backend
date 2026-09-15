"""OAuth tests."""

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import OrganizationProfile, SpeakerProfile
from users.models import User
from users.views import oauth_views


class OAuthTests(TestCase):
    """Test OAuth flows."""

    def setUp(self):
        """Test setup."""
        self.client = APIClient()
        self.github_login_url = reverse("users:github-login")
        self.github_callback_url = reverse("users:github-callback")
        self.google_login_url = reverse("users:google-login")
        self.google_callback_url = reverse("users:google-callback")
        # Ensure callbacks will redirect instead of raising Http404
        oauth_views.frontend_url = "http://test-frontend"

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
        # Trigger the callback view which should create the user
        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        user = User.objects.get(email="test@github.com")
        self.assertEqual(user.username, "githubuser")
        # No profile is auto-created on signup; only the user is returned.
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
        # Trigger the callback view which should create the user
        response = self.client.get(
            self.google_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        user = User.objects.get(email="test@google.com")
        self.assertEqual(user.username, "Google User")


class OAuthProfileDataTests(TestCase):
    """Tests that OAuth callbacks detect and return the user's profiles."""

    def setUp(self):
        """Set up a client and callback URLs."""
        self.client = APIClient()
        self.github_callback_url = reverse("users:github-callback")
        self.google_callback_url = reverse("users:google-callback")
        oauth_views.frontend_url = "http://test-frontend"

    def _user_param(self, response) -> dict:
        """Extract and decode the `user` query parameter from a redirect URL."""
        params = parse_qs(urlparse(response.url).query)
        return json.loads(params["user"][0])

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_returns_profiles_for_new_user(self, mock_get_session):
        """A newly created OAuth user gets their profiles reported."""
        mock_github = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_profile@example.com", "login": "ghprofile"}
        ]

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        profiles = self._user_param(response)["profile"]
        # Signup does not auto-create a profile; a new user has neither type.
        self.assertEqual(profiles, {})

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_marks_new_user_email_verified(self, mock_get_session):
        """A user created via GitHub OAuth skips OTP verification."""
        mock_github = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_verified@example.com", "login": "ghverified"}
        ]

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        user = User.objects.get(email="gh_verified@example.com")
        self.assertTrue(user.is_email_verified)
        self.assertTrue(self._user_param(response)["is_email_verified"])

    @patch("users.views.oauth_views.get_github_session")
    def test_github_callback_verifies_existing_email_user(self, mock_get_session):
        """A returning OAuth login verifies an email/password account's email."""
        user = User.objects.create(
            email="gh_existing@example.com",
            username="ghexisting",
            is_email_verified=False,
        )
        mock_github = mock_get_session.return_value
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_existing@example.com", "login": "ghexisting"}
        ]

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
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
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_github.fetch_token.return_value = {"access_token": "token"}
        mock_github.get.return_value.json.side_effect = [
            {"email": "gh_existing@example.com", "login": "ghexisting"}
        ]

        response = self.client.get(
            self.github_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        profiles = self._user_param(response)["profile"]
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
        session = self.client.session
        session["oauth_state"] = "test_state"
        session.save()
        mock_google.fetch_token.return_value = {"access_token": "token"}
        mock_google.get.return_value.json.return_value = {
            "email": "gl_existing@example.com",
            "name": "gl_existing",
        }

        response = self.client.get(
            self.google_callback_url, {"code": "code", "state": "test_state"}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        profiles = self._user_param(response)["profile"]
        self.assertIsNotNone(profiles["organization_profile"])
        self.assertEqual(profiles["organization_profile"]["name"], "Acme Org")
        self.assertNotIn("speaker_profile", profiles)
