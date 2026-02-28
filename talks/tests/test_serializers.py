"""test talks serializers."""

from django.test import TestCase
from rest_framework.test import APIClient

from talks.serializers import TalkReviewCommentSerializer


class TestTalkReviewCommentSerializer(TestCase):
    """Test TalkReviewCommentSerializer."""

    def setUp(self):
        """Set up test data."""
        comment_payload = {
            "talk": None,
            "rating": 5,
            "comment": "This is a test comment.",
        }
        self.client = APIClient()
        self.serializer = TalkReviewCommentSerializer(data=comment_payload)
        self.serializer.is_valid()

    def test_talk_review_comment_serializer_fields(self):
        """Test that the serializer contains the expected fields."""
        expected_fields = {"id", "talk", "rating", "comment"}
        self.assertEqual(set(self.serializer.fields.keys()), expected_fields)

    def test_talk_review_comment_serializer_is_valid(self):
        """Test that the serializer is valid."""
        self.assertTrue(self.serializer.is_valid())

    def test_talk_review_comment_serializer_data(self):
        """Test that the serializer data is correct."""
        expected_data = {
            "talk": None,
            "rating": 5,
            "comment": "This is a test comment.",
        }

        self.assertEqual(self.serializer.data, expected_data)
