"""speakers app tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from speakers.models import (
    SpeakerExperiences,
    SpeakerProfile,
    SpeakerSkillTag,
    SpeakerSocialLinks,
)
from speakers.serializers import SpeakerProfileSerializer


class TestSpeakerProfile(TestCase):
    """test speaker profile models, views and serializers."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create(
            username="testuser",
            email="user@mail.com",
            password="testpass123",
        )
        self.skill_tag = SpeakerSkillTag.objects.create(
            name="Django", description="Web framework", duration=5
        )

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.user,
            short_bio="This is a test bio.",
            long_bio="This is a longer test bio for the speaker profile.",
            organization="Test Org",
            country="Test Country",
        )
        self.speaker_profile.skill_tag.set([self.skill_tag])
        self.speaker_social_link = SpeakerSocialLinks.objects.create(
            speaker=self.speaker_profile,
            name="Twitter",
            link="https://twitter.com/testuser",
        )

    def test_speaker_profile_creation(self):
        """Test speaker profile creation."""
        assert self.speaker_profile.user_account.username == "testuser"
        assert self.speaker_profile.organization == "Test Org"
        assert self.speaker_profile.country == "Test Country"
        assert self.speaker_profile.skill_tag.count() == 1
        assert self.speaker_profile.skill_tag.first().name == "Django"
        assert self.speaker_profile.short_bio == "This is a test bio."
        assert (
            self.speaker_profile.long_bio
            == "This is a longer test bio for the speaker profile."
        )

    def test_speaker_profile_serializer(self):
        """Test speaker profile serializer."""
        serializer = SpeakerProfileSerializer(instance=self.speaker_profile)
        data = serializer.data
        assert data["user_account"] == self.user.id
        assert data["organization"] == "Test Org"
        assert data["country"] == "Test Country"
        assert len(data["skill_tag"]) == 1
        assert data["skill_tag"][0]["id"] == self.skill_tag.id
        assert len(data["social_links"]) == 1
        assert data["social_links"][0]["name"] == "Twitter"
        assert data["social_links"][0]["link"] == "https://twitter.com/testuser"

    def test_speaker_skill_tag_creation(self):
        """Test speaker skill tag creation."""
        assert self.skill_tag.name == "Django"
        assert self.skill_tag.description == "Web framework"
        assert self.skill_tag.duration == 5

    def test_speaker_social_links_creation(self):
        """Test speaker social links creation."""
        assert self.speaker_social_link.name == "Twitter"
        assert self.speaker_social_link.link == "https://twitter.com/testuser"
        assert self.speaker_social_link.speaker == self.speaker_profile

        assert self.speaker_profile.social_links.count() == 1
        assert self.speaker_profile.social_links.first().name == "Twitter"
        assert (
            self.speaker_profile.social_links.first().link
            == "https://twitter.com/testuser"
        )


class TestSpeakerExperiences(TestCase):
    """test speaker experiences models, views and serializers."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create(
            username="expuser",
            email="expuser@mail.com",
            password="testpass123",
        )
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.user,
            short_bio="Experience test bio.",
            long_bio="Longer experience test bio for the speaker profile.",
            organization="Experience Test Org",
            country="Experience Test Country",
        )
        self.speaker_experiences = SpeakerExperiences.objects.create(
            event_name="Tech Conference",
            event_date="2023-01-15",
            topic="Django Testing",
            description="Presented on testing in Django applications.",
            presentation_link="https://slides.com/expuser/django-testing",
            video_recording_link="https://youtube.com/watch?v=expuser123",
        )
        self.speaker_profile.experiences.set([self.speaker_experiences])

    def test_speaker_experiences_creation(self):
        """Test speaker experiences creation."""
        assert self.speaker_experiences.event_name == "Tech Conference"
        assert self.speaker_experiences.event_date == "2023-01-15"
        assert self.speaker_experiences.topic == "Django Testing"
        assert (
            self.speaker_experiences.description
            == "Presented on testing in Django applications."
        )
        assert (
            self.speaker_experiences.presentation_link
            == "https://slides.com/expuser/django-testing"
        )
        assert (
            self.speaker_experiences.video_recording_link
            == "https://youtube.com/watch?v=expuser123"
        )

    def test_speaker_profile_experiences_association(self):
        """Test association between speaker profile and experiences."""
        assert self.speaker_profile.experiences.count() == 1
        experience = self.speaker_profile.experiences.first()
        assert experience.event_name == "Tech Conference"
        assert experience.topic == "Django Testing"

    def test_speaker_experiences_serializer(self):
        """Test speaker experiences serializer."""
        from speakers.serializers import SpeakerExperiencesSerializer

        serializer = SpeakerExperiencesSerializer(instance=self.speaker_experiences)
        data = serializer.data
        assert data["event_name"] == "Tech Conference"
        assert data["event_date"] == "2023-01-15"
        assert data["topic"] == "Django Testing"
        assert data["description"] == "Presented on testing in Django applications."
        assert data["presentation_link"] == "https://slides.com/expuser/django-testing"
        assert data["video_recording_link"] == "https://youtube.com/watch?v=expuser123"
