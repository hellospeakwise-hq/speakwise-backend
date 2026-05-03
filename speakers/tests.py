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
        assert data["skill_tags"][0]["id"] == str(self.skill_tags.id)
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


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerFollow model tests
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerFollowModelTests(TestCase):
    """Tests for the SpeakerFollow model."""

    def setUp(self):
        """Create two users and one speaker profile."""
        User = get_user_model()
        self.speaker_user = User.objects.create(
            username="speaker_one",
            email="speaker@example.com",
            password="pass123",
        )
        self.follower_user = User.objects.create(
            username="follower_one",
            email="follower@example.com",
            password="pass123",
        )
        self.profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="TestOrg",
            short_bio="Short bio.",
        )

    def test_follow_creation(self):
        """A SpeakerFollow record is created correctly."""
        from speakers.models import SpeakerFollow

        follow = SpeakerFollow.objects.create(
            follower=self.follower_user,
            speaker=self.profile,
        )
        self.assertEqual(follow.follower, self.follower_user)
        self.assertEqual(follow.speaker, self.profile)
        self.assertIn(self.follower_user.username, str(follow))

    def test_followers_count_property(self):
        """followers_count reflects the number of SpeakerFollow records."""
        from speakers.models import SpeakerFollow

        self.assertEqual(self.profile.followers_count, 0)

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        self.assertEqual(self.profile.followers_count, 1)

    def test_unique_together_prevents_duplicate_follow(self):
        """A user cannot follow the same speaker twice."""
        from django.db import IntegrityError

        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        with self.assertRaises(IntegrityError):
            SpeakerFollow.objects.create(
                follower=self.follower_user, speaker=self.profile
            )

    def test_follow_deleted_on_user_delete(self):
        """Deleting a user cascades to their SpeakerFollow records."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        self.assertEqual(SpeakerFollow.objects.count(), 1)

        self.follower_user.delete()
        self.assertEqual(SpeakerFollow.objects.count(), 0)

    def test_follow_deleted_on_speaker_profile_delete(self):
        """Deleting a speaker profile cascades to its SpeakerFollow records."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        self.assertEqual(SpeakerFollow.objects.count(), 1)

        self.profile.delete()
        self.assertEqual(SpeakerFollow.objects.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerProfileSerializer — followers_count & is_following fields
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerProfileSerializerFollowFieldsTests(TestCase):
    """Test that SpeakerProfileSerializer exposes follow-related fields."""

    def setUp(self):
        """Create speaker and follower users."""
        User = get_user_model()
        self.speaker_user = User.objects.create(
            username="ser_speaker",
            email="ser_speaker@example.com",
            password="pass123",
        )
        self.follower_user = User.objects.create(
            username="ser_follower",
            email="ser_follower@example.com",
            password="pass123",
        )
        self.profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="Serializer Org",
        )

    def test_followers_count_is_zero_initially(self):
        """followers_count is 0 when no one follows."""
        serializer = SpeakerProfileSerializer(
            instance=self.profile, context={"request": None}
        )
        self.assertEqual(serializer.data["followers_count"], 0)

    def test_followers_count_increments_after_follow(self):
        """followers_count reflects actual follow records."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        serializer = SpeakerProfileSerializer(
            instance=self.profile, context={"request": None}
        )
        self.assertEqual(serializer.data["followers_count"], 1)

    def test_is_following_false_when_no_request(self):
        """is_following is False when no request context is provided."""
        serializer = SpeakerProfileSerializer(
            instance=self.profile, context={"request": None}
        )
        self.assertFalse(serializer.data["is_following"])

    def test_is_following_true_for_follower(self):
        """is_following is True for an authenticated user who follows the speaker."""
        from django.test import RequestFactory

        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)

        request = RequestFactory().get("/")
        request.user = self.follower_user

        serializer = SpeakerProfileSerializer(
            instance=self.profile, context={"request": request}
        )
        self.assertTrue(serializer.data["is_following"])

    def test_is_following_false_for_non_follower(self):
        """is_following is False for an authenticated user who does not follow."""
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.follower_user  # has NOT followed

        serializer = SpeakerProfileSerializer(
            instance=self.profile, context={"request": request}
        )
        self.assertFalse(serializer.data["is_following"])


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerFollowView API tests  —  GET / POST / DELETE  /speakers/<slug>/follow/
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerFollowViewTests(APITestCase):
    """Tests for SpeakerFollowView (follow / unfollow / status)."""

    def setUp(self):
        """Create speaker user, follower user, and speaker profile."""
        self.client = APIClient()
        User = get_user_model()

        self.speaker_user = User.objects.create(
            username="view_speaker",
            email="view_speaker@example.com",
            password="pass123",
        )
        self.follower_user = User.objects.create(
            username="view_follower",
            email="view_follower@example.com",
            password="pass123",
        )
        self.other_user = User.objects.create(
            username="view_other",
            email="view_other@example.com",
            password="pass123",
        )
        self.profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="View Org",
        )
        self.follow_url = reverse(
            "speakers:speaker_follow", kwargs={"slug": self.profile.slug}
        )

    # ── Authentication guard ────────────────────────────────────────────────

    def test_unauthenticated_get_returns_401(self):
        """GET /follow/ requires authentication."""
        res = self.client.get(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_post_returns_401(self):
        """POST /follow/ requires authentication."""
        res = self.client.post(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_returns_401(self):
        """DELETE /follow/ requires authentication."""
        res = self.client.delete(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── GET — check follow status ────────────────────────────────────────────

    def test_get_follow_status_not_following(self):
        """GET returns is_following=False when user has not followed."""
        self.client.force_authenticate(self.follower_user)
        res = self.client.get(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data["is_following"])
        self.assertEqual(res.data["followers_count"], 0)

    def test_get_follow_status_is_following(self):
        """GET returns is_following=True after the user followed."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        self.client.force_authenticate(self.follower_user)
        res = self.client.get(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["is_following"])
        self.assertEqual(res.data["followers_count"], 1)

    def test_get_follow_status_invalid_slug_returns_404(self):
        """GET with an invalid slug returns 404."""
        self.client.force_authenticate(self.follower_user)
        url = reverse("speakers:speaker_follow", kwargs={"slug": "no-such-speaker"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ── POST — follow ────────────────────────────────────────────────────────

    def test_post_follow_creates_record(self):
        """POST creates a SpeakerFollow record and returns 201."""
        from speakers.models import SpeakerFollow

        self.client.force_authenticate(self.follower_user)
        res = self.client.post(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["followers_count"], 1)
        self.assertTrue(
            SpeakerFollow.objects.filter(
                follower=self.follower_user, speaker=self.profile
            ).exists()
        )

    def test_post_follow_twice_returns_400(self):
        """POST a second time returns 400 'already following'."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        self.client.force_authenticate(self.follower_user)
        res = self.client.post(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already following", res.data["detail"].lower())

    def test_post_self_follow_returns_400(self):
        """A speaker cannot follow their own profile."""
        self.client.force_authenticate(self.speaker_user)
        res = self.client.post(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot follow yourself", res.data["detail"].lower())

    def test_post_follow_updates_followers_count(self):
        """followers_count in the response reflects the new total."""
        self.client.force_authenticate(self.follower_user)
        res = self.client.post(self.follow_url)
        self.assertEqual(res.data["followers_count"], 1)

        # A second user follows as well
        self.client.force_authenticate(self.other_user)
        res = self.client.post(self.follow_url)
        self.assertEqual(res.data["followers_count"], 2)

    # ── DELETE — unfollow ────────────────────────────────────────────────────

    def test_delete_unfollow_removes_record(self):
        """DELETE removes the SpeakerFollow record and returns 200."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        self.client.force_authenticate(self.follower_user)
        res = self.client.delete(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["followers_count"], 0)
        self.assertFalse(
            SpeakerFollow.objects.filter(
                follower=self.follower_user, speaker=self.profile
            ).exists()
        )

    def test_delete_unfollow_when_not_following_returns_400(self):
        """DELETE when not following returns 400 'not following'."""
        self.client.force_authenticate(self.follower_user)
        res = self.client.delete(self.follow_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not following", res.data["detail"].lower())

    def test_delete_unfollow_decrements_followers_count(self):
        """followers_count drops by 1 after unfollowing."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_user, speaker=self.profile)
        SpeakerFollow.objects.create(follower=self.other_user, speaker=self.profile)

        self.client.force_authenticate(self.follower_user)
        res = self.client.delete(self.follow_url)
        self.assertEqual(res.data["followers_count"], 1)


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerFollowersListView API tests  —  GET  /speakers/<slug>/followers/
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerFollowersListViewTests(APITestCase):
    """Tests for SpeakerFollowersListView (public follower list)."""

    def setUp(self):
        """Create users, a speaker profile, and a few follow records."""
        self.client = APIClient()
        User = get_user_model()

        self.speaker_user = User.objects.create(
            username="list_speaker",
            email="list_speaker@example.com",
            password="pass123",
        )
        self.follower_a = User.objects.create(
            username="follower_a",
            email="follower_a@example.com",
            password="pass123",
        )
        self.follower_b = User.objects.create(
            username="follower_b",
            email="follower_b@example.com",
            password="pass123",
        )
        self.profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="List Org",
        )
        self.list_url = reverse(
            "speakers:speaker_followers_list", kwargs={"slug": self.profile.slug}
        )

    def test_followers_list_is_public(self):
        """Unauthenticated users can view the followers list."""
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_followers_list_empty_initially(self):
        """Empty followers list returns count=0 and empty list."""
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["followers_count"], 0)
        self.assertEqual(res.data["followers"], [])

    def test_followers_list_shows_all_followers(self):
        """All follower records appear in the response."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.follower_a, speaker=self.profile)
        SpeakerFollow.objects.create(follower=self.follower_b, speaker=self.profile)

        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["followers_count"], 2)
        self.assertEqual(len(res.data["followers"]), 2)

        usernames = {f["username"] for f in res.data["followers"]}
        self.assertIn("follower_a", usernames)
        self.assertIn("follower_b", usernames)

    def test_followers_list_invalid_slug_returns_404(self):
        """Invalid slug returns 404."""
        url = reverse("speakers:speaker_followers_list", kwargs={"slug": "ghost-slug"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# following_count bug-fix tests
# Verifies that following_count always reflects the VIEWED speaker's count,
# not the logged-in user's count.
# ─────────────────────────────────────────────────────────────────────────────


class FollowingCountFixTests(APITestCase):
    """Regression tests for the following_count bug fix.

    Before the fix, following_count returned how many speakers the
    *logged-in user* follows — instead of how many the *viewed speaker* follows.
    These tests assert the corrected behaviour across GET, POST, and DELETE.
    """

    def setUp(self):
        """Create three users (A, B, C) and matching speaker profiles."""
        self.client = APIClient()
        User = get_user_model()

        self.user_a = User.objects.create(
            username="user_a", email="a@example.com", password="pass"
        )
        self.user_b = User.objects.create(
            username="user_b", email="b@example.com", password="pass"
        )
        self.user_c = User.objects.create(
            username="user_c", email="c@example.com", password="pass"
        )

        self.profile_a = SpeakerProfile.objects.create(
            user_account=self.user_a, organization="Org A"
        )
        self.profile_b = SpeakerProfile.objects.create(
            user_account=self.user_b, organization="Org B"
        )
        self.profile_c = SpeakerProfile.objects.create(
            user_account=self.user_c, organization="Org C"
        )

        # speaker_a's follow URL
        self.follow_a_url = reverse(
            "speakers:speaker_follow", kwargs={"slug": self.profile_a.slug}
        )

    # ── GET /speakers/<slug>/follow/ ────────────────────────────────────────

    def test_get_following_count_reflects_viewed_speaker_not_logged_in_user(self):
        """GET following_count = views speaker's following count, not caller's."""
        from speakers.models import SpeakerFollow

        # user_a follows profile_b and profile_c (profile_a follows 2)
        SpeakerFollow.objects.create(follower=self.user_a, speaker=self.profile_b)
        SpeakerFollow.objects.create(follower=self.user_a, speaker=self.profile_c)

        # user_b follows nobody (0 following), but we authenticate as user_b
        # and hit the profile_a view endpoint
        self.client.force_authenticate(self.user_b)
        res = self.client.get(self.follow_a_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Must show profile_a's following count (2), NOT user_b's following count (0)
        self.assertEqual(res.data["following_count"], 2)

    # ── POST /speakers/<slug>/follow/ ───────────────────────────────────────

    def test_post_following_count_reflects_viewed_speaker_not_logged_in_user(self):
        """POST following_count = viewed speaker's following count, not caller's."""
        from speakers.models import SpeakerFollow

        # user_a follows profile_c (profile_a's following count = 1)
        SpeakerFollow.objects.create(follower=self.user_a, speaker=self.profile_c)

        # user_b follows nobody → authenticate as user_b and follow profile_a
        self.client.force_authenticate(self.user_b)
        res = self.client.post(self.follow_a_url)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # following_count should be profile_a's count (1), NOT user_b's (0)
        self.assertEqual(res.data["following_count"], 1)
        # followers_count of profile_a should now be 1 (user_b just followed)
        self.assertEqual(res.data["followers_count"], 1)

    # ── DELETE /speakers/<slug>/follow/ ─────────────────────────────────────

    def test_delete_following_count_reflects_viewed_speaker_not_logged_in_user(self):
        """DELETE following_count = viewed speaker's following count, not caller's."""
        from speakers.models import SpeakerFollow

        # user_a follows profile_b and profile_c (profile_a's following count = 2)
        SpeakerFollow.objects.create(follower=self.user_a, speaker=self.profile_b)
        SpeakerFollow.objects.create(follower=self.user_a, speaker=self.profile_c)

        # user_b follows profile_a, then unfollows
        SpeakerFollow.objects.create(follower=self.user_b, speaker=self.profile_a)
        self.client.force_authenticate(self.user_b)
        res = self.client.delete(self.follow_a_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # following_count should be profile_a's count (2), NOT user_b's (0)
        self.assertEqual(res.data["following_count"], 2)
        # followers_count of profile_a should now be 0
        self.assertEqual(res.data["followers_count"], 0)

    # ── Serializer ───────────────────────────────────────────────────────────

    def test_serializer_exposes_following_count(self):
        """SpeakerProfileSerializer now includes following_count field."""
        from speakers.models import SpeakerFollow

        SpeakerFollow.objects.create(follower=self.user_a, speaker=self.profile_b)

        serializer = SpeakerProfileSerializer(
            instance=self.profile_a, context={"request": None}
        )
        self.assertIn("following_count", serializer.data)
        self.assertEqual(serializer.data["following_count"], 1)

    def test_serializer_following_count_zero_when_speaker_follows_nobody(self):
        """following_count is 0 when the speaker follows no one."""
        serializer = SpeakerProfileSerializer(
            instance=self.profile_b, context={"request": None}
        )
        self.assertEqual(serializer.data["following_count"], 0)


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerDeck model tests
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerDeckModelTests(TestCase):
    """Tests for the SpeakerDeck model."""

    def setUp(self):
        """Create user, speaker profile, and event."""
        User = get_user_model()
        self.user = User.objects.create(
            username="deck_speaker",
            email="deck_speaker@example.com",
            password="pass123",
        )
        self.profile = SpeakerProfile.objects.create(
            user_account=self.user,
            organization="Deck Org",
        )
        from events.models import Event

        self.event = Event.objects.create(
            title="Deck Conference",
            is_active=True,
            speaker_deck_upload_enabled=True,
        )

    def test_speaker_deck_creation(self):
        """A SpeakerDeck record is created correctly."""
        from speakers.models import SpeakerDeck

        deck = SpeakerDeck.objects.create(
            speaker=self.profile,
            event=self.event,
            file="speaker_decks/test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            description="My presentation",
        )
        self.assertEqual(deck.speaker, self.profile)
        self.assertEqual(deck.event, self.event)
        self.assertEqual(deck.original_filename, "test.pdf")
        self.assertEqual(deck.file_size, 1024)
        self.assertEqual(deck.description, "My presentation")
        self.assertIn("test.pdf", str(deck))

    def test_speaker_deck_cascade_on_speaker_delete(self):
        """Deleting a speaker profile cascades to its SpeakerDeck records."""
        from speakers.models import SpeakerDeck

        SpeakerDeck.objects.create(
            speaker=self.profile,
            event=self.event,
            file="speaker_decks/test.pdf",
            original_filename="test.pdf",
            file_size=1024,
        )
        self.assertEqual(SpeakerDeck.objects.count(), 1)
        self.profile.delete()
        self.assertEqual(SpeakerDeck.objects.count(), 0)

    def test_speaker_deck_cascade_on_event_delete(self):
        """Deleting an event cascades to its SpeakerDeck records."""
        from speakers.models import SpeakerDeck

        SpeakerDeck.objects.create(
            speaker=self.profile,
            event=self.event,
            file="speaker_decks/test.pdf",
            original_filename="test.pdf",
            file_size=1024,
        )
        self.assertEqual(SpeakerDeck.objects.count(), 1)
        self.event.delete()
        self.assertEqual(SpeakerDeck.objects.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# Notification model tests
# ─────────────────────────────────────────────────────────────────────────────


class NotificationModelTests(TestCase):
    """Tests for the Notification model."""

    def setUp(self):
        """Create a user for notifications."""
        User = get_user_model()
        self.user = User.objects.create(
            username="notif_user",
            email="notif@example.com",
            password="pass123",
        )

    def test_notification_creation(self):
        """A Notification record is created correctly."""
        from speakers.models import Notification

        notif = Notification.objects.create(
            recipient=self.user,
            title="Test Notification",
            message="This is a test.",
            link="https://example.com/test",
        )
        self.assertEqual(notif.recipient, self.user)
        self.assertEqual(notif.title, "Test Notification")
        self.assertFalse(notif.is_read)
        self.assertIn("Test Notification", str(notif))
        self.assertIn(self.user.username, str(notif))

    def test_notification_default_is_unread(self):
        """Notifications default to is_read=False."""
        from speakers.models import Notification

        notif = Notification.objects.create(
            recipient=self.user,
            title="Unread Test",
            message="Should be unread by default.",
        )
        self.assertFalse(notif.is_read)

    def test_notification_cascade_on_user_delete(self):
        """Deleting a user cascades to their notifications."""
        from speakers.models import Notification

        Notification.objects.create(
            recipient=self.user,
            title="Cascade Test",
            message="Should be deleted with user.",
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Notification.objects.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerDeck serializer validation tests
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerDeckSerializerTests(TestCase):
    """Tests for SpeakerDeckSerializer file validation."""

    def test_valid_file_types_accepted(self):
        """Supported file types pass validation."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from speakers.serializers import SpeakerDeckSerializer

        for ext in [".pdf", ".pptx", ".ppt", ".key", ".odp", ".zip"]:
            filename = f"test{ext}"
            file = SimpleUploadedFile(
                filename, b"fake content", content_type="application/octet-stream"
            )
            serializer = SpeakerDeckSerializer(data={"file": file})
            # We can't fully validate without event/speaker, but validate_file should pass
            # Test the field-level validation directly
            validated = serializer.fields["file"].run_validation(file)
            self.assertIsNotNone(validated)

    def test_invalid_file_type_rejected(self):
        """Unsupported file types are rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from speakers.serializers import SpeakerDeckSerializer

        file = SimpleUploadedFile(
            "test.exe", b"fake content", content_type="application/octet-stream"
        )
        serializer = SpeakerDeckSerializer(data={"file": file})
        # validate_file is called during is_valid
        is_valid = serializer.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("file", serializer.errors)

    def test_file_too_large_rejected(self):
        """Files exceeding 50 MB are rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from speakers.serializers import SpeakerDeckSerializer

        # Create a file just over the limit
        large_content = b"x" * (50 * 1024 * 1024 + 1)
        file = SimpleUploadedFile(
            "large.pdf", large_content, content_type="application/pdf"
        )
        serializer = SpeakerDeckSerializer(data={"file": file})
        is_valid = serializer.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("file", serializer.errors)


# ─────────────────────────────────────────────────────────────────────────────
# SpeakerDeck API view tests
# ─────────────────────────────────────────────────────────────────────────────


class SpeakerDeckViewTests(APITestCase):
    """Tests for SpeakerDeckListCreateView and SpeakerDeckRetrieveUpdateDestroyView."""

    def setUp(self):
        """Create users, speaker profile, event, organization, and accepted request."""
        self.client = APIClient()
        User = get_user_model()

        # Speaker user
        self.speaker_user = User.objects.create(
            username="deck_view_speaker",
            email="deck_view@example.com",
            password="pass123",
        )
        self.speaker_profile = SpeakerProfile.objects.create(
            user_account=self.speaker_user,
            organization="Deck View Org",
        )

        # Non-speaker user (has no speaker profile)
        self.other_user = User.objects.create(
            username="deck_view_other",
            email="deck_other@example.com",
            password="pass123",
        )

        # Non-accepted speaker
        self.rejected_user = User.objects.create(
            username="rejected_speaker",
            email="rejected@example.com",
            password="pass123",
        )
        self.rejected_profile = SpeakerProfile.objects.create(
            user_account=self.rejected_user,
            organization="Rejected Org",
        )

        # Organization
        from organizations.models import Organization

        self.organization = Organization.objects.create(
            name="Deck View Org",
            email="deckorg@example.com",
            created_by=self.other_user,
        )

        # Event with uploads enabled
        from events.models import Event

        self.event = Event.objects.create(
            title="Deck View Conference",
            is_active=True,
            speaker_deck_upload_enabled=True,
            organizer=self.organization,
        )

        # Event with uploads disabled
        self.event_disabled = Event.objects.create(
            title="Disabled Conference",
            is_active=True,
            speaker_deck_upload_enabled=False,
            organizer=self.organization,
        )

        # Accepted speaker request
        from speakerrequests.models import SpeakerRequest

        SpeakerRequest.objects.create(
            organizer=self.organization,
            speaker=self.speaker_profile,
            event=self.event,
            status="accepted",
            message="Welcome!",
        )

        # Rejected speaker request
        SpeakerRequest.objects.create(
            organizer=self.organization,
            speaker=self.rejected_profile,
            event=self.event,
            status="rejected",
            message="Sorry.",
        )

        self.list_url = reverse("speakers:speaker_decks_list_create")

    def _make_file(self, name="presentation.pdf", size=1024):
        """Create a SimpleUploadedFile for testing."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(
            name, b"x" * size, content_type="application/octet-stream"
        )

    # ── Authentication ──────────────────────────────────────────────────────

    def test_unauthenticated_get_returns_401(self):
        """GET without auth returns 401."""
        res = self.client.get(self.list_url, {"event": str(self.event.id)})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_post_returns_401(self):
        """POST without auth returns 401."""
        res = self.client.post(self.list_url, {"event": str(self.event.id)})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Missing event parameter ─────────────────────────────────────────────

    def test_get_without_event_param_returns_400(self):
        """GET without event query param returns 400."""
        self.client.force_authenticate(self.speaker_user)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_without_event_param_returns_400(self):
        """POST without event query param returns 400."""
        self.client.force_authenticate(self.speaker_user)
        file = self._make_file()
        res = self.client.post(self.list_url, {"file": file}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── No speaker profile ──────────────────────────────────────────────────

    def test_post_without_speaker_profile_returns_403(self):
        """User without a speaker profile cannot upload."""
        self.client.force_authenticate(self.other_user)
        file = self._make_file()
        res = self.client.post(
            f"{self.list_url}?event={self.event.id}",
            {"file": file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── Upload disabled ─────────────────────────────────────────────────────

    def test_post_when_upload_disabled_returns_403(self):
        """Cannot upload when speaker_deck_upload_enabled is False."""
        # Create accepted request for disabled event
        from speakerrequests.models import SpeakerRequest

        SpeakerRequest.objects.create(
            organizer=self.organization,
            speaker=self.speaker_profile,
            event=self.event_disabled,
            status="accepted",
            message="Welcome!",
        )

        self.client.force_authenticate(self.speaker_user)
        file = self._make_file()
        res = self.client.post(
            f"{self.list_url}?event={self.event_disabled.id}",
            {"file": file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not enabled", res.data["detail"].lower())

    # ── Not accepted ────────────────────────────────────────────────────────

    def test_post_when_not_accepted_returns_403(self):
        """Cannot upload when speaker is not accepted for the event."""
        self.client.force_authenticate(self.rejected_user)
        file = self._make_file()
        res = self.client.post(
            f"{self.list_url}?event={self.event.id}",
            {"file": file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("accepted speaker", res.data["detail"].lower())

    # ── Successful upload ───────────────────────────────────────────────────

    def test_post_successful_upload(self):
        """Accepted speaker can upload a deck when uploads are enabled."""
        self.client.force_authenticate(self.speaker_user)
        file = self._make_file("my_talk.pptx", 2048)
        res = self.client.post(
            f"{self.list_url}?event={self.event.id}",
            {"file": file, "description": "My keynote slides"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["original_filename"], "my_talk.pptx")
        self.assertEqual(res.data["file_size"], 2048)
        self.assertEqual(res.data["description"], "My keynote slides")
        self.assertEqual(res.data["event"], str(self.event.id))

    def test_post_multiple_uploads_allowed(self):
        """Multiple deck uploads are allowed for the same event."""
        self.client.force_authenticate(self.speaker_user)
        file1 = self._make_file("talk_v1.pdf", 1024)
        file2 = self._make_file("talk_v2.pdf", 2048)

        res1 = self.client.post(
            f"{self.list_url}?event={self.event.id}",
            {"file": file1},
            format="multipart",
        )
        res2 = self.client.post(
            f"{self.list_url}?event={self.event.id}",
            {"file": file2},
            format="multipart",
        )
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    # ── List decks ──────────────────────────────────────────────────────────

    def test_get_lists_only_own_decks(self):
        """GET returns only the authenticated speaker's decks for the event."""
        from speakers.models import SpeakerDeck

        SpeakerDeck.objects.create(
            speaker=self.speaker_profile,
            event=self.event,
            file="speaker_decks/mine.pdf",
            original_filename="mine.pdf",
            file_size=512,
        )

        self.client.force_authenticate(self.speaker_user)
        res = self.client.get(f"{self.list_url}?event={self.event.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["original_filename"], "mine.pdf")

    # ── Detail CRUD ─────────────────────────────────────────────────────────

    def test_detail_get_patch_delete(self):
        """Detail view supports GET, PATCH, DELETE for own decks."""
        from speakers.models import SpeakerDeck

        deck = SpeakerDeck.objects.create(
            speaker=self.speaker_profile,
            event=self.event,
            file="speaker_decks/crud.pdf",
            original_filename="crud.pdf",
            file_size=512,
        )
        detail_url = reverse("speakers:speaker_deck_detail", kwargs={"pk": deck.id})

        self.client.force_authenticate(self.speaker_user)

        # GET
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["original_filename"], "crud.pdf")

        # PATCH description
        res = self.client.patch(
            detail_url, {"description": "Updated desc"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        deck.refresh_from_db()
        self.assertEqual(deck.description, "Updated desc")

        # DELETE
        res = self.client.delete(detail_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        from speakers.models import SpeakerDeck as SD

        self.assertFalse(SD.objects.filter(id=deck.id).exists())

    def test_detail_other_user_gets_404(self):
        """Other users cannot access another speaker's deck."""
        from speakers.models import SpeakerDeck

        deck = SpeakerDeck.objects.create(
            speaker=self.speaker_profile,
            event=self.event,
            file="speaker_decks/private.pdf",
            original_filename="private.pdf",
            file_size=512,
        )
        detail_url = reverse("speakers:speaker_deck_detail", kwargs={"pk": deck.id})

        self.client.force_authenticate(self.rejected_user)
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# Notification API view tests
# ─────────────────────────────────────────────────────────────────────────────


class NotificationViewTests(APITestCase):
    """Tests for NotificationListView and NotificationMarkReadView."""

    def setUp(self):
        """Create users and notifications."""
        self.client = APIClient()
        User = get_user_model()

        self.user = User.objects.create(
            username="notif_view_user",
            email="notifview@example.com",
            password="pass123",
        )
        self.other_user = User.objects.create(
            username="notif_other",
            email="notifother@example.com",
            password="pass123",
        )

        from speakers.models import Notification

        self.notif1 = Notification.objects.create(
            recipient=self.user,
            title="Upload Your Deck",
            message="Please upload your presentation.",
            link="https://example.com/upload",
        )
        self.notif2 = Notification.objects.create(
            recipient=self.user,
            title="Reminder",
            message="Don't forget to upload.",
            is_read=True,
        )
        # Another user's notification (should not appear)
        self.notif_other = Notification.objects.create(
            recipient=self.other_user,
            title="Other's Notification",
            message="Not for you.",
        )

        self.list_url = reverse("speakers:notification_list")

    # ── Authentication ──────────────────────────────────────────────────────

    def test_unauthenticated_get_returns_401(self):
        """GET without auth returns 401."""
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── List ────────────────────────────────────────────────────────────────

    def test_list_returns_only_own_notifications(self):
        """GET returns only the authenticated user's notifications."""
        self.client.force_authenticate(self.user)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        titles = {n["title"] for n in res.data}
        self.assertIn("Upload Your Deck", titles)
        self.assertIn("Reminder", titles)
        self.assertNotIn("Other's Notification", titles)

    def test_list_filter_unread(self):
        """GET ?is_read=false returns only unread notifications."""
        self.client.force_authenticate(self.user)
        res = self.client.get(f"{self.list_url}?is_read=false")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Upload Your Deck")

    def test_list_filter_read(self):
        """GET ?is_read=true returns only read notifications."""
        self.client.force_authenticate(self.user)
        res = self.client.get(f"{self.list_url}?is_read=true")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Reminder")

    # ── Mark as read ────────────────────────────────────────────────────────

    def test_mark_read_success(self):
        """PATCH marks a notification as read."""
        mark_url = reverse(
            "speakers:notification_mark_read", kwargs={"pk": self.notif1.id}
        )
        self.client.force_authenticate(self.user)
        res = self.client.patch(mark_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["is_read"])
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_read_other_users_notification_returns_404(self):
        """Cannot mark another user's notification as read."""
        mark_url = reverse(
            "speakers:notification_mark_read", kwargs={"pk": self.notif_other.id}
        )
        self.client.force_authenticate(self.user)
        res = self.client.patch(mark_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_read_nonexistent_returns_404(self):
        """PATCH on non-existent notification returns 404."""
        import uuid

        mark_url = reverse(
            "speakers:notification_mark_read", kwargs={"pk": uuid.uuid4()}
        )
        self.client.force_authenticate(self.user)
        res = self.client.patch(mark_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
