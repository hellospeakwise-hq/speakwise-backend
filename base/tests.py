"""Base app tests."""

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from base.validators import validate_image_extension, validate_image_size


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


class PaginationEnforcementTests(APITestCase):
    """List endpoints must return a bounded paginated envelope."""

    def test_blog_list_is_paginated(self):
        """A catalog list never returns an unbounded array."""
        response = self.client.get(reverse("blogs:blog-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

    def test_event_list_is_paginated(self):
        """Event catalog returns count/next/results, not a raw list."""
        response = self.client.get(reverse("events:event-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

    def test_unauthenticated_list_is_still_paginated(self):
        """Anonymous catalog reads are bounded the same way."""
        self.client.logout()
        response = self.client.get(reverse("events:event-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)


class ApiErrorShapeTests(APITestCase):
    """Errors return client-safe JSON, never HTML pages."""

    def test_404_returns_json_detail(self):
        """Unknown API routes return JSON with a code, not HTML."""
        from django.test import override_settings

        with override_settings(DEBUG=False):
            response = self.client.get("/api/nonexistent-endpoint-xyz/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("detail", response.json())

    def test_validation_error_preserves_field_messages(self):
        """Field errors keep per-field messages so clients can render them."""
        client = APIClient()
        response = client.post(
            reverse("blogs:blog-list-create"), {"short_description": "No title"}
        )
        # Anonymous POST is rejected before validation; force auth to reach it.
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="errshape", email="errshape@mail.com", password="pass12345"
        )
        client.force_authenticate(user=user)
        response = client.post(
            reverse("blogs:blog-list-create"), {"short_description": "No title"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)


class UploadValidatorTests(APITestCase):
    """File upload guards reject dangerous or oversized payloads."""

    def test_rejects_disallowed_extension(self):
        """An .exe upload is rejected even with valid image bytes."""
        evil = SimpleUploadedFile("evil.exe", b"not-an-image", "application/x-ms")
        with self.assertRaises(ValidationError):
            validate_image_extension(evil)

    def test_rejects_oversized_image(self):
        """Images over 5MB are rejected before reaching storage."""
        big = SimpleUploadedFile("big.jpg", b"x" * (6 * 1024 * 1024), "image/jpeg")
        with self.assertRaises(ValidationError):
            validate_image_size(big)
