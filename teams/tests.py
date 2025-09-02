"""Teams app tests."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from teams.models import TeamMember, TeamSocial
from teams.serializers import TeamMemberSerializer, TeamSocialSerializer


class TestTeamModels(TestCase):
    """Test Team models."""

    def setUp(self):
        """Set up test data."""
        self.team_member = TeamMember.objects.create(
            name="John Doe",
            role="Software Engineer",
            short_bio="An experienced software engineer specializing in web development.",
            display_order=1,
            is_active=True,
        )

        self.team_social = TeamSocial.objects.create(
            team_member=self.team_member,
            name="LinkedIn",
            link="https://linkedin.com/in/johndoe",
        )

    def test_team_member_creation(self):
        """Test TeamMember model creation."""
        assert self.team_member.name == "John Doe"
        assert self.team_member.role == "Software Engineer"
        assert (
            self.team_member.short_bio
            == "An experienced software engineer specializing in web development."
        )
        assert self.team_member.display_order == 1
        assert self.team_member.is_active is True
        assert str(self.team_member) == "John Doe - Software Engineer"

    def test_team_member_avatar_url_property_without_avatar(self):
        """Test avatar_url property when no avatar is set."""
        assert self.team_member.avatar_url is None

    def test_team_member_avatar_url_property_with_avatar(self):
        """Test avatar_url property when avatar is set."""
        fake_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"fake_image_content",
            content_type="image/jpeg",
        )
        self.team_member.avatar = fake_image
        self.team_member.save()

        assert self.team_member.avatar_url is not None
        assert "test_image" in self.team_member.avatar_url

    def test_team_social_creation(self):
        """Test TeamSocial model creation."""
        assert self.team_social.name == "LinkedIn"
        assert self.team_social.link == "https://linkedin.com/in/johndoe"
        assert self.team_social.team_member == self.team_member
        assert str(self.team_social) == "LinkedIn - John Doe"

    def test_team_member_social_links_relationship(self):
        """Test the relationship between TeamMember and TeamSocial."""
        assert self.team_member.social_links.count() == 1
        assert self.team_member.social_links.first() == self.team_social

    def test_team_member_ordering(self):
        """Test TeamMember model ordering."""
        team_member2 = TeamMember.objects.create(
            name="Jane Smith",
            role="Product Manager",
            short_bio="Experienced product manager.",
            display_order=0,
            is_active=True,
        )

        team_members = list(TeamMember.objects.all())
        assert team_members[0] == team_member2  # display_order=0 comes first
        assert team_members[1] == self.team_member  # display_order=1 comes second


class TestTeamSerializers(TestCase):
    """Test Team serializers."""

    def setUp(self):
        """Set up test data."""
        self.team_member = TeamMember.objects.create(
            name="Alice Johnson",
            role="UI/UX Designer",
            short_bio="Creative designer with 5 years of experience.",
            display_order=2,
            is_active=True,
        )

        self.team_social1 = TeamSocial.objects.create(
            team_member=self.team_member,
            name="Twitter",
            link="https://twitter.com/alicejohnson",
        )

        self.team_social2 = TeamSocial.objects.create(
            team_member=self.team_member,
            name="Dribbble",
            link="https://dribbble.com/alicejohnson",
        )

    def test_team_social_serializer(self):
        """Test TeamSocialSerializer."""
        serializer = TeamSocialSerializer(instance=self.team_social1)
        data = serializer.data

        expected_fields = {"name", "link"}
        assert set(data.keys()) == expected_fields
        assert data["name"] == "Twitter"
        assert data["link"] == "https://twitter.com/alicejohnson"

    def test_team_member_serializer_contains_expected_fields(self):
        """Test that TeamMemberSerializer contains expected fields."""
        serializer = TeamMemberSerializer(instance=self.team_member)
        data = serializer.data

        expected_fields = {
            "id",
            "name",
            "role",
            "short_bio",
            "avatar",
            "avatar_url",
            "display_order",
            "social_links",
        }
        assert set(data.keys()) == expected_fields

    def test_team_member_serializer_field_content(self):
        """Test TeamMemberSerializer field content."""
        serializer = TeamMemberSerializer(instance=self.team_member)
        data = serializer.data

        assert data["name"] == "Alice Johnson"
        assert data["role"] == "UI/UX Designer"
        assert data["short_bio"] == "Creative designer with 5 years of experience."
        assert data["display_order"] == 2
        assert data["avatar_url"] is None  # No avatar uploaded
        assert len(data["social_links"]) == 2

    def test_team_member_serializer_social_links(self):
        """Test TeamMemberSerializer includes social links."""
        serializer = TeamMemberSerializer(instance=self.team_member)
        data = serializer.data

        social_links = data["social_links"]
        assert len(social_links) == 2

        # Check that both social links are included
        social_names = [link["name"] for link in social_links]
        assert "Twitter" in social_names
        assert "Dribbble" in social_names

    def test_team_member_serializer_avatar_url_with_request_context(self):
        """Test avatar_url method with request context."""
        from django.test import RequestFactory

        request = RequestFactory().get("/api/teams/")
        request.META["HTTP_HOST"] = "testserver"

        serializer = TeamMemberSerializer(
            instance=self.team_member, context={"request": request}
        )
        data = serializer.data

        # Should be None since no avatar is set
        assert data["avatar_url"] is None


class TestTeamMemberListView(APITestCase):
    """Test TeamMemberListView API endpoint."""

    def setUp(self):
        """Set up test data."""
        # Create active team members
        self.active_member1 = TeamMember.objects.create(
            name="Bob Wilson",
            role="Backend Developer",
            short_bio="Expert in Django and Python development.",
            display_order=1,
            is_active=True,
        )

        self.active_member2 = TeamMember.objects.create(
            name="Carol Davis",
            role="Frontend Developer",
            short_bio="React and Vue.js specialist.",
            display_order=0,  # Should appear first due to ordering
            is_active=True,
        )

        # Create inactive team member (should not appear in API)
        self.inactive_member = TeamMember.objects.create(
            name="Dave Smith",
            role="Former Developer",
            short_bio="No longer with the company.",
            display_order=2,
            is_active=False,
        )

        # Add social links to active members
        TeamSocial.objects.create(
            team_member=self.active_member1,
            name="GitHub",
            link="https://github.com/bobwilson",
        )

        TeamSocial.objects.create(
            team_member=self.active_member2,
            name="Portfolio",
            link="https://caroldavis.dev",
        )

    def test_get_team_members_success(self):
        """Test successful retrieval of active team members."""
        url = reverse("teams:team-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return only active members
        assert len(data) == 2

        # Check ordering (display_order, then name)
        assert data[0]["name"] == "Carol Davis"  # display_order=0
        assert data[1]["name"] == "Bob Wilson"  # display_order=1

    def test_get_team_members_includes_social_links(self):
        """Test that response includes social links."""
        url = reverse("teams:team-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Find Bob Wilson's data
        bob_data = next(
            (member for member in data if member["name"] == "Bob Wilson"), None
        )
        assert bob_data is not None
        assert len(bob_data["social_links"]) == 1
        assert bob_data["social_links"][0]["name"] == "GitHub"
        assert bob_data["social_links"][0]["link"] == "https://github.com/bobwilson"

    def test_get_team_members_excludes_inactive(self):
        """Test that inactive members are excluded."""
        url = reverse("teams:team-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify inactive member is not included
        member_names = [member["name"] for member in data]
        assert "Dave Smith" not in member_names
        assert len(data) == 2  # Only active members

    def test_get_team_members_response_structure(self):
        """Test the structure of team member response."""
        url = reverse("teams:team-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check first team member has all expected fields
        first_member = data[0]
        expected_fields = {
            "id",
            "name",
            "role",
            "short_bio",
            "avatar",
            "avatar_url",
            "display_order",
            "social_links",
        }
        assert set(first_member.keys()) == expected_fields

    def test_get_team_members_with_no_data(self):
        """Test API response when no active team members exist."""
        # Make all members inactive
        TeamMember.objects.update(is_active=False)

        url = reverse("teams:team-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Empty list

    def test_prefetch_optimization(self):
        """Test that social links are prefetched (no N+1 queries)."""
        url = reverse("teams:team-list")

        # This should execute only 2 queries:
        # 1. Get team members
        # 2. Prefetch social links
        with self.assertNumQueries(2):
            response = self.client.get(url)
            response.json()  # Force serialization

        assert response.status_code == status.HTTP_200_OK
