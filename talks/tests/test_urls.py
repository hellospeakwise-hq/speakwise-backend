"""test talks urls."""

from django.test import TestCase
from django.urls import resolve, reverse
from rest_framework.test import APIClient

from talks.views import TalkReviewCommentListCreateView


class TestTalkReviewCommentListCreateViewURL(TestCase):
    """test talk review comment list create view url."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # use a dummy talk_id when reversing; the reverse function doesn't query the DB
        self.talk_id = 1
        self.url = reverse(
            "talks:talk-review-comment-list",
            kwargs={"talk_id": self.talk_id},
        )

    def test_talk_review_comment_list_create_view_url(self):
        """Test url."""
        expected = f"/api/talks/{self.talk_id}/talk-review-comments/"
        self.assertEqual(self.url, expected)

    def test_talk_review_comment_list_create_view_resolves(self):
        """Test url resolves to correct view."""
        view = resolve(f"/api/talks/{self.talk_id}/talk-review-comments/")
        self.assertEqual(view.func.view_class, TalkReviewCommentListCreateView)
        self.assertEqual(view.view_name, "talks:talk-review-comment-list")
        self.assertEqual(view.url_name, "talk-review-comment-list")
