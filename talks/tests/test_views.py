"""test talks views."""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from events.models import Country, Event, Location
from speakers.models import SpeakerProfile
from talks.models import Talks
from talks.views import TalkReviewCommentListCreateView
from users.models import User


class TestTalkReviewCommentListCreateView(TestCase):
    """test talk review comment list create view."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # create related objects so we can build a real talk and use its id
        self.user = User.objects.create(
            username="viewuser",
            first_name="View",
            last_name="User",
            email="viewuser@mail.com",
            password="testpass",
        )
        self.speaker_profile = SpeakerProfile.objects.create(user_account=self.user)
        self.talk = Talks.objects.create(
            title="View Test Talk",
            description="A talk used in view tests.",
            speaker=self.speaker_profile,
            duration=30,
            category="frontend",
            event=Event.objects.create(
                title="View Event",
                description="Event for view tests",
                location=Location.objects.create(
                    venue="Venue",
                    address="Addr",
                    city="City",
                    state="State",
                    country=Country.objects.create(name="Country"),
                ),
            ),
        )
        self.url = reverse(
            "talks:talk-review-comment-list",
            kwargs={"talk_id": self.talk.id},
        )
        self.view = TalkReviewCommentListCreateView.as_view()

    def test_talk_review_comment_list_create_view_get(self):
        """Test get request."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_talk_review_comment_list_create_view_post(self):
        """Test post request."""
        payload = {"talk": self.talk.id, "comment": "This is a test comment."}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
