"""CFP model tests."""

from django.db import IntegrityError
from django.test import TestCase

from cfp.choices import AudienceLevelChoices, CFPStatusChoices, TalkTypeChoices
from cfp.models import CFPSubmission
from events.models import Country, Event, Location
from organizations.models import Organization, OrganizationMembership
from users.models import User


class CFPSubmissionModelTest(TestCase):
    """Test CFPSubmission model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="speaker1",
            email="speaker1@test.com",
            password="testpass",
        )
        self.org = Organization.objects.create(
            name="TestOrg", email="testorg@test.com", created_by=self.user
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role="ADMIN", added_by=self.user
        )
        self.event = Event.objects.create(
            title="PyCon Test",
            description="Test event",
            location=Location.objects.create(
                venue="Venue",
                address="Addr",
                city="City",
                state="State",
                country=Country.objects.create(name="Ghana"),
            ),
            organizer=self.org,
        )
        self.submission = CFPSubmission.objects.create(
            event=self.event,
            submitter=self.user,
            talk_type=TalkTypeChoices.SHORT,
            audience=AudienceLevelChoices.BEGINNER,
            category="frontend",
            elevator_pitch="A quick pitch.",
            abstract="Full abstract here.",
        )

    def test_submission_created(self):
        """Test that a submission is created correctly."""
        assert self.submission.id is not None
        assert self.submission.talk_type == TalkTypeChoices.SHORT
        assert self.submission.audience == AudienceLevelChoices.BEGINNER
        assert self.submission.category == "frontend"
        assert self.submission.elevator_pitch == "A quick pitch."
        assert self.submission.abstract == "Full abstract here."
        assert self.submission.submitter == self.user
        assert self.submission.event == self.event

    def test_default_status_is_pending(self):
        """Test that the default status is pending."""
        assert self.submission.status == CFPStatusChoices.PENDING

    def test_str_representation(self):
        """Test the string representation of the submission."""
        assert str(self.submission) == f"{self.user} — {self.event.title}"

    def test_unique_together_enforced(self):
        """Test that a user cannot submit more than once per event."""
        with self.assertRaises(IntegrityError):
            CFPSubmission.objects.create(
                event=self.event,
                submitter=self.user,
                talk_type=TalkTypeChoices.LONG,
                audience=AudienceLevelChoices.ADVANCED,
                category="backend",
                elevator_pitch="Another pitch.",
                abstract="Another abstract.",
            )
