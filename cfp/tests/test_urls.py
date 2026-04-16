"""CFP URL tests."""

from django.test import TestCase
from django.urls import resolve, reverse
from rest_framework.test import APIClient

from cfp.views import CFPStatusUpdateView, CFPSubmissionDetailView, CFPSubmissionListCreateView


class CFPURLTest(TestCase):
    """Test CFP URL patterns resolve to the correct views."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.event_slug = "pycon-ghana-2026"
        self.submission_id = "00000000-0000-0000-0000-000000000001"

    def test_cfp_list_create_url(self):
        """Test the CFP list/create URL."""
        url = reverse("cfp:cfp-list-create", kwargs={"slug": self.event_slug})
        self.assertEqual(url, f"/api/events/{self.event_slug}/cfp/")

    def test_cfp_list_create_resolves(self):
        """Test that the CFP list/create URL resolves to the correct view."""
        view = resolve(f"/api/events/{self.event_slug}/cfp/")
        self.assertEqual(view.func.view_class, CFPSubmissionListCreateView)
        self.assertEqual(view.url_name, "cfp-list-create")

    def test_cfp_detail_url(self):
        """Test the CFP detail URL."""
        url = reverse("cfp:cfp-detail", kwargs={"pk": self.submission_id})
        self.assertEqual(url, f"/api/cfp/{self.submission_id}/")

    def test_cfp_detail_resolves(self):
        """Test that the CFP detail URL resolves to the correct view."""
        view = resolve(f"/api/cfp/{self.submission_id}/")
        self.assertEqual(view.func.view_class, CFPSubmissionDetailView)
        self.assertEqual(view.url_name, "cfp-detail")

    def test_cfp_status_update_url(self):
        """Test the CFP status update URL."""
        url = reverse("cfp:cfp-status-update", kwargs={"pk": self.submission_id})
        self.assertEqual(url, f"/api/cfp/{self.submission_id}/status/")

    def test_cfp_status_update_resolves(self):
        """Test that the CFP status update URL resolves to the correct view."""
        view = resolve(f"/api/cfp/{self.submission_id}/status/")
        self.assertEqual(view.func.view_class, CFPStatusUpdateView)
        self.assertEqual(view.url_name, "cfp-status-update")
