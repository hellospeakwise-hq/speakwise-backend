"""speakers app tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

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
        self.skill_tags = SpeakerSkillTag.objects.create(
            name="Django", description="Web framework", duration=5
        )

        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.user,
            short_bio="This is a test bio.",
            long_bio="This is a longer test bio for the speaker profile.",
            organization="Test Org",
            country="Test Country",
        )
        self.speaker_profile.skill_tag.set([self.skill_tags])
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
        assert len(data["skill_tags"]) == 1
        assert data["skill_tags"][0]["id"] == self.skill_tags.id
        assert len(data["social_links"]) == 1
        assert data["social_links"][0]["name"] == "Twitter"
        assert data["social_links"][0]["link"] == "https://twitter.com/testuser"

    def test_speaker_skill_tag_creation(self):
        """Test speaker skill tag creation."""
        assert self.skill_tags.name == "Django"
        assert self.skill_tags.description == "Web framework"
        assert self.skill_tags.duration == 5

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
        assert data["topic"] == "Django Testing"
        assert data["description"] == "Presented on testing in Django applications."
        assert data["presentation_link"] == "https://slides.com/expuser/django-testing"
        assert data["video_recording_link"] == "https://youtube.com/watch?v=expuser123"


class PublicSpeakerExperiencesViewTests(APITestCase):
    """Tests for PublicSpeakerExperiencesListView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Create user and speaker profile
        self.user = get_user_model().objects.create(
            username="publicuser",
            email="public@example.com",
            password="testpass123",
        )
        self.profile = SpeakerProfile.objects.create(
            user_account=self.user,
            organization="Public Org",
        )
        # Create an experience for this profile
        self.exp = SpeakerExperiences.objects.create(
            speaker=self.profile,
            event_name="Public Conf",
            event_date="2024-06-01",
            topic="Public Speaking",
            description="Great talk",
            presentation_link="https://slides.example.com/pub",
            video_recording_link="https://video.example.com/pub",
        )
        self.url = reverse(
            "speakers:public_speaker_experiences", kwargs={"slug": self.profile.slug}
        )

    def test_public_experiences_by_slug(self):
        """Should return experiences for the given speaker slug."""
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["event_name"], "Public Conf")
        self.assertEqual(res.data[0]["topic"], "Public Speaking")

    def test_public_experiences_invalid_slug_returns_empty(self):
        """Invalid slug should return empty list (200)."""
        url = reverse(
            "speakers:public_speaker_experiences", kwargs={"slug": "unknown-slug"}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])


class SpeakerSkillTagsViewsTests(APITestCase):
    """Tests for SpeakerSkillTagsListView and SpeakerSkillTagsDetailView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Two users and their profiles
        self.u1 = get_user_model().objects.create(
            username="alice",
            email="alice@example.com",
            password="testpass123",
        )
        self.u2 = get_user_model().objects.create(
            username="bob",
            email="bob@example.com",
            password="testpass123",
        )
        self.p1 = SpeakerProfile.objects.create(
            user_account=self.u1, organization="Org1"
        )
        self.p2 = SpeakerProfile.objects.create(
            user_account=self.u2, organization="Org2"
        )

        # Existing tags
        self.t1 = SpeakerSkillTag.objects.create(
            speaker=self.p1, name="Django", description="Web", duration=5
        )
        self.t2 = SpeakerSkillTag.objects.create(
            speaker=self.p2, name="Flask", description="Web", duration=3
        )

        self.list_url = reverse("speakers:skills_list")

    def test_list_requires_authentication(self):
        """List view requires authentication."""
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_authenticated_users_tags(self):
        """List view returns only tags associated with authenticated user."""
        self.client.force_authenticate(self.u1)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "Django")

    def test_create_skill_tag_associates_with_user_profile(self):
        """Create view creates a tag associated with authenticated user's profile."""
        self.client.force_authenticate(self.u1)
        payload = {"name": "Python", "description": "Lang", "duration": 10}
        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Verify created in DB and linked to p1
        created = (
            SpeakerSkillTag.objects.get(id=res.data["id"])
            if "id" in res.data
            else SpeakerSkillTag.objects.get(name="Python", speaker=self.p1)
        )
        # Ensure the created tag is linked to the authenticated user's speaker profile
        self.assertEqual(created.speaker.user_account_id, self.u1.id)
        self.assertEqual(created.name, "Python")

    def test_detail_get_patch_delete_for_own_tag(self):
        """Detail view allows GET, PATCH and DELETE for own tags."""
        self.client.force_authenticate(self.u1)
        detail_url = reverse("speakers:skills_detail", kwargs={"pk": self.t1.id})

        # GET own tag
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Django")

        # PATCH update
        res = self.client.patch(
            detail_url, {"name": "Django Pro", "duration": 6}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.name, "Django Pro")
        self.assertEqual(self.t1.duration, 6)

        # DELETE
        res = self.client.delete(detail_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SpeakerSkillTag.objects.filter(id=self.t1.id).exists())

    def test_cannot_access_others_tags(self):
        """Detail view returns 404 for other users' tags."""
        self.client.force_authenticate(self.u1)
        other_detail_url = reverse("speakers:skills_detail", kwargs={"pk": self.t2.id})

        # GET other's tag -> 404
        res = self.client.get(other_detail_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # PATCH other's tag -> 404
        res = self.client.patch(other_detail_url, {"name": "Hack"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # DELETE other's tag -> 404
        res = self.client.delete(other_detail_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
