"""CFP model tests."""

from django.test import TestCase

from cfps.choices import AudienceLevelChoices, CFPStatusChoices, TalkTypeChoices
from cfps.models import CFPSubmission
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
        """Test the string representation uses the submission title."""
        self.submission.title = "My Great Talk"
        self.submission.save()
        assert str(self.submission) == f"{self.user} — My Great Talk"

    def test_multiple_submissions_per_event_allowed(self):
        """Test that a user can submit more than one CFP per event."""
        second = CFPSubmission.objects.create(
            event=self.event,
            submitter=self.user,
            talk_type=TalkTypeChoices.LONG,
            audience=AudienceLevelChoices.ADVANCED,
            category="backend",
            elevator_pitch="A second pitch.",
            abstract="A second abstract.",
        )
        assert second.id is not None
        assert (
            CFPSubmission.objects.filter(event=self.event, submitter=self.user).count()
            == 2
        )

    def test_new_fields_have_correct_defaults(self):
        """Test that the new CFP fields default correctly."""
        assert self.submission.title == ""
        assert self.submission.duration is None
        assert self.submission.language == "English"
        assert self.submission.outline == ""
        assert self.submission.slides_url is None
        assert self.submission.recording_url is None
        assert self.submission.notes_for_organizers == ""
        assert self.submission.is_first_time_speaker is False
        assert self.submission.travel_support_needed is False
