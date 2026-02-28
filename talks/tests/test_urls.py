"""test talks urls."""

from django.test import TestCase
from django.urls import resolve, reverse
from rest_framework.test import APIClient

from talks.views import TalkReviewSubmitView


class TestTalkReviewSubmitViewURL(TestCase):
    """test talk review submit view url."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # use a dummy slug when reversing; the reverse function doesn't query the DB
        self.slug = "test-slug-123"
        self.url = reverse(
            "talks:talk-review-submit",
            kwargs={"slug": self.slug},
        )

    def test_talk_review_submit_view_url(self):
        """Test url."""
        expected = f"/api/talks/{self.slug}/reviews/"
        self.assertEqual(self.url, expected)

    def test_talk_review_submit_view_resolves(self):
        """Test url resolves to correct view."""
        view = resolve(f"/api/talks/{self.slug}/reviews/")
        self.assertEqual(view.func.view_class, TalkReviewSubmitView)
        self.assertEqual(view.view_name, "talks:talk-review-submit")
        self.assertEqual(view.url_name, "talk-review-submit")
