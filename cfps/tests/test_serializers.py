"""CFP serializer tests."""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from cfps.choices import AudienceLevelChoices, CFPStatusChoices, TalkTypeChoices
from cfps.models import CFPSubmission
from cfps.serializers import CFPStatusUpdateSerializer, CFPSubmissionSerializer
from events.models import Country, Event, Location
from organizations.models import Organization, OrganizationMembership
from users.models import User


class CFPSubmissionSerializerTest(TestCase):
    """Test CFPSubmissionSerializer."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="speaker",
            email="speaker@test.com",
            password="testpass",
        )
        self.org = Organization.objects.create(
            name="SerializerOrg", email="serializerorg@test.com", created_by=self.user
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role="ADMIN", added_by=self.user
        )
        self.event = Event.objects.create(
            title="Serializer Event",
            description="desc",
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
            audience=AudienceLevelChoices.ALL,
            category="frontend",
            elevator_pitch="Short pitch.",
            abstract="Full abstract.",
        )
        self.serializer = CFPSubmissionSerializer(instance=self.submission)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields."""
        self.assertEqual(
            set(self.serializer.data.keys()),
            {
                "id",
                "event",
                "event_slug",
                "event_title",
                "submitter",
                "submitter_email",
                "title",
                "talk_type",
                "duration",
                "audience",
                "category",
                "language",
                "elevator_pitch",
                "abstract",
                "outline",
                "slides_url",
                "recording_url",
                "co_speakers",
                "co_speakers_detail",
                "other_speakers_text",
                "notes_for_organizers",
                "other_comments",
                "is_first_time_speaker",
                "travel_support_needed",
                "status",
            },
        )

    def test_event_slug_and_title_are_read_only(self):
        """Test that event_slug and event_title are present and read-only."""
        data = self.serializer.data
        self.assertEqual(data["event_slug"], self.event.slug)
        self.assertEqual(data["event_title"], self.event.title)

    def test_new_fields_serialized_correctly(self):
        """Test title, duration, language, outline and flag fields serialize correctly."""
        self.submission.title = "New Talk"
        self.submission.duration = 30
        self.submission.language = "French"
        self.submission.is_first_time_speaker = True
        self.submission.travel_support_needed = True
        self.submission.save()
        data = CFPSubmissionSerializer(instance=self.submission).data
        self.assertEqual(data["title"], "New Talk")
        self.assertEqual(data["duration"], 30)
        self.assertEqual(data["language"], "French")
        self.assertTrue(data["is_first_time_speaker"])
        self.assertTrue(data["travel_support_needed"])

    def test_title_is_stripped_on_validate(self):
        """Test that leading/trailing whitespace is stripped from title."""
        serializer = CFPSubmissionSerializer(
            instance=self.submission, data={"title": "  Padded Title  "}, partial=True
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["title"], "Padded Title")

    def test_field_content(self):
        """Test that the serializer field content is correct."""
        data = self.serializer.data
        self.assertEqual(data["elevator_pitch"], self.submission.elevator_pitch)
        self.assertEqual(data["abstract"], self.submission.abstract)
        self.assertEqual(data["talk_type"], TalkTypeChoices.SHORT)
        self.assertEqual(data["status"], CFPStatusChoices.PENDING)

    def test_status_is_read_only(self):
        """Test that status cannot be set by the submitter."""
        serializer = CFPSubmissionSerializer(
            instance=self.submission,
            data={"status": CFPStatusChoices.ACCEPTED},
            partial=True,
        )
        serializer.is_valid()
        self.assertNotIn("status", serializer.validated_data)

    def test_update_blocked_when_not_pending(self):
        """Test that editing is blocked once a submission is no longer pending."""
        self.submission.status = CFPStatusChoices.ACCEPTED
        self.submission.save()
        serializer = CFPSubmissionSerializer(
            instance=self.submission,
            data={"elevator_pitch": "Updated pitch."},
            partial=True,
        )
        serializer.is_valid()
        with self.assertRaises(ValidationError):
            serializer.save()

    def test_invalid_talk_type(self):
        """Test that an invalid talk type raises a validation error."""
        serializer = CFPSubmissionSerializer(
            data={"talk_type": "keynote"}, partial=True
        )
        serializer.is_valid()
        self.assertIn("talk_type", serializer.errors)

    def test_invalid_category(self):
        """Test that an invalid category raises a validation error."""
        serializer = CFPSubmissionSerializer(
            data={"category": "not_a_category"}, partial=True
        )
        serializer.is_valid()
        self.assertIn("category", serializer.errors)


class CFPStatusUpdateSerializerTest(TestCase):
    """Test CFPStatusUpdateSerializer."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_only_status_field(self):
        """Test that the serializer only contains the status field."""
        serializer = CFPStatusUpdateSerializer(data={"status": "accepted"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(set(serializer.fields.keys()), {"status"})

    def test_invalid_status(self):
        """Test that an invalid status raises a validation error."""
        serializer = CFPStatusUpdateSerializer(data={"status": "maybe"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
