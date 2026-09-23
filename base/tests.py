"""Base app tests."""

from unittest.mock import patch

from django.db import OperationalError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckViewTests(APITestCase):
    """Test the public health endpoint."""

    def test_returns_ok_with_database_status(self):
        """A healthy API reports ok for both the app and Postgres."""
        response = self.client.get(reverse("base:health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "ok")

    def test_unauthenticated_request_is_allowed(self):
        """Railway probes carry no credentials, so the endpoint is public."""
        self.client.logout()
        response = self.client.get(reverse("base:health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unreachable_database_returns_503(self):
        """A Postgres outage surfaces as 503 so Railway stops routing traffic."""
        with patch(
            "base.views.connection.ensure_connection",
            side_effect=OperationalError("down"),
        ):
            response = self.client.get(reverse("base:health"))
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["database"], "unavailable")
