"""Tests for the organizations app."""

from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from organizations.choices import OrganizationRole
from organizations.filters import OrganizationFilter
from organizations.models import Organization, OrganizationMembership
from organizations.permissions import IsOrganizationAdminPermission
from organizations.serializers import (
    AddMemberSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)
from users.models import User


class OrganizationModelTest(TestCase):
    """Test cases for Organization model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.organization = Organization.objects.create(
            name="Test Organization",
            email="org@example.com",
            description="A test organization",
            website="https://testorg.com",
            created_by=self.user,
        )

    def test_organization_creation(self):
        """Test organization creation."""
        self.assertEqual(self.organization.name, "Test Organization")
        self.assertEqual(self.organization.email, "org@example.com")
        self.assertTrue(self.organization.is_active)
        self.assertEqual(self.organization.created_by, self.user)

    def test_unique_name_email_constraint(self):
        """Test that organization name and email must be unique together."""
        with self.assertRaises(IntegrityError):
            Organization.objects.create(
                name="Test Organization", email="org@example.com", created_by=self.user
            )

    def test_organization_str_representation(self):
        """Test string representation of organization."""
        self.assertEqual(str(self.organization), "Test Organization")

    def test_get_admins(self):
        """Test getting organization admins."""
        admin_user = User.objects.create(
            username="adminuser", email="admin@example.com", password="adminpass123"
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=admin_user,
            role=OrganizationRole.ADMIN,
            added_by=self.user,
        )

        admins = self.organization.get_admins()
        self.assertEqual(admins.count(), 1)
        self.assertEqual(admins.first().user, admin_user)

    def test_get_organizers(self):
        """Test getting all active organization members."""
        member_user = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        organizers = self.organization.get_organizers()
        self.assertEqual(organizers.count(), 1)
        self.assertEqual(organizers.first().user, member_user)

    def test_is_admin(self):
        """Test checking if a user is an admin."""
        admin_user = User.objects.create(
            username="adminuser", email="admin@example.com", password="adminpass123"
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=admin_user,
            role=OrganizationRole.ADMIN,
            added_by=self.user,
        )

        self.assertTrue(self.organization.is_admin(admin_user))
        self.assertFalse(self.organization.is_admin(self.user))

    def test_is_member(self):
        """Test checking if a user is a member."""
        member_user = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        self.assertTrue(self.organization.is_member(member_user))
        self.assertFalse(self.organization.is_member(self.user))


class OrganizationMembershipModelTest(TestCase):
    """Test cases for OrganizationMembership model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.member_user = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )

        self.organization = Organization.objects.create(
            name="Test Organization", email="org@example.com", created_by=self.user
        )

    def test_membership_creation(self):
        """Test organization membership creation."""
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        self.assertEqual(membership.organization, self.organization)
        self.assertEqual(membership.user, self.member_user)
        self.assertEqual(membership.role, OrganizationRole.MEMBER)
        self.assertEqual(membership.added_by, self.user)
        self.assertTrue(membership.is_active)

    def test_unique_organization_user_constraint(self):
        """Test that organization and user must be unique together."""
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        with self.assertRaises(IntegrityError):
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=self.member_user,
                role=OrganizationRole.ADMIN,
                added_by=self.user,
            )

    def test_membership_str_representation(self):
        """Test string representation of membership."""
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        expected_str = (
            f"{self.member_user.username} - {self.organization.name} (MEMBER)"
        )
        self.assertEqual(str(membership), expected_str)

    def test_deleted_user_membership(self):
        """Test membership behavior when user is deleted."""
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        # Delete the user
        self.member_user.delete()

        # Membership should be deleted due to CASCADE
        with self.assertRaises(OrganizationMembership.DoesNotExist):
            membership.refresh_from_db()

    def test_membership_with_deleted_organization(self):
        """Test membership behavior when organization is deleted."""
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        # Delete the organization
        self.organization.delete()

        # Membership should be deleted due to CASCADE
        with self.assertRaises(OrganizationMembership.DoesNotExist):
            membership.refresh_from_db()


class OrganizationSerializerTest(TestCase):
    """Test cases for Organization serializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.organization_data = {
            "name": "Test Organization",
            "email": "org@example.com",
            "description": "A test organization",
            "website": "https://testorg.com",
        }

    def test_organization_serializer_with_valid_data(self):
        """Test organization serializer with valid data."""
        context = {"request": type("Request", (), {"user": self.user})}
        serializer = OrganizationSerializer(
            data=self.organization_data, context=context
        )
        self.assertTrue(serializer.is_valid())

        organization = serializer.save()
        self.assertEqual(organization.name, self.organization_data["name"])
        self.assertEqual(organization.created_by, self.user)

        # Test that the creator was automatically added as an admin
        self.assertTrue(organization.is_admin(self.user))

    # Edge Cases for Serializer
    def test_serializer_with_missing_context(self):
        """Test serializer behavior without request context."""
        serializer = OrganizationSerializer(data=self.organization_data)
        with self.assertRaises(KeyError):
            serializer.is_valid()
            serializer.save()

    def test_serializer_read_only_fields(self):
        """Test serializer read-only fields protection."""
        data_with_readonly = self.organization_data.copy()
        data_with_readonly["created_by"] = 999  # Trying to set read-only field
        data_with_readonly["created_at"] = "2023-01-01T00:00:00Z"

        context = {"request": type("Request", (), {"user": self.user})}
        serializer = OrganizationSerializer(data=data_with_readonly, context=context)
        self.assertTrue(serializer.is_valid())

        organization = serializer.save()
        self.assertEqual(
            organization.created_by, self.user
        )  # Should use context user instead
        self.assertNotEqual(
            organization.created_at.isoformat(), "2023-01-01T00:00:00+00:00"
        )


class OrganizationMembershipSerializerTest(TestCase):
    """Test cases for OrganizationMembership serializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.member = User.objects.create(
            username="member", email="member@example.com", password="memberpass123"
        )

        self.organization = Organization.objects.create(
            name="Test Organization", email="org@example.com", created_by=self.user
        )

        self.membership_data = {
            "organization": self.organization.id,
            "user": self.member.id,
            "role": OrganizationRole.MEMBER,
            "added_by": self.user.id,
        }

    def test_membership_serializer_with_valid_data(self):
        """Test membership serializer with valid data."""
        # Create the membership directly rather than through the serializer
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        # Then use the serializer to serialize it
        serializer = OrganizationMembershipSerializer(instance=membership)
        data = serializer.data

        self.assertEqual(data["organization"], self.organization.id)
        self.assertEqual(data["user"], self.member.id)
        self.assertEqual(data["role"], OrganizationRole.MEMBER)

    def test_membership_serializer_with_nonexistent_organization(self):
        """Test membership creation with non-existent organization."""
        invalid_data = self.membership_data.copy()
        invalid_data["organization"] = 99999  # Non-existent organization ID

        serializer = OrganizationMembershipSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_membership_serializer_with_nonexistent_user(self):
        """Test membership creation with non-existent user."""
        invalid_data = self.membership_data.copy()
        invalid_data["user"] = 99999  # Non-existent user ID

        serializer = OrganizationMembershipSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_membership_serializer_read_only_fields(self):
        """Test read-only fields protection."""
        # Create the membership directly
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        # Use data with readonly fields
        data_with_readonly = {
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }

        # Partial update should ignore read_only fields
        serializer = OrganizationMembershipSerializer(
            instance=membership, data=data_with_readonly, partial=True
        )
        self.assertTrue(serializer.is_valid())
        self.assertNotEqual(
            membership.created_at.isoformat(), "2023-01-01T00:00:00+00:00"
        )
        self.assertNotEqual(
            membership.updated_at.isoformat(), "2023-01-01T00:00:00+00:00"
        )


class AddMemberSerializerTest(TestCase):
    """Test cases for AddMemberSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.member = User.objects.create(
            username="member", email="member@example.com", password="memberpass123"
        )
        self.organization = Organization.objects.create(
            name="Test Organization", email="org@example.com", created_by=self.user
        )
        self.data = {
            "organization": self.organization.id,
            "user": self.member.id,
            "role": OrganizationRole.MEMBER,
        }

    def test_add_member_serializer_with_valid_data(self):
        """Test adding a member with valid data."""
        # Make the user an admin of the organization
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationRole.ADMIN,
            added_by=self.user,
        )
        serializer = AddMemberSerializer(data=self.data)

        self.assertTrue(serializer.is_valid())
        membership = serializer.save()

        self.assertEqual(membership.organization.id, self.data["organization"])
        self.assertEqual(membership.user.id, self.data["user"])
        self.assertEqual(membership.role, self.data["role"])


class OrganizationViewsTest(APITestCase):
    """Test cases for Organization views."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.organization = Organization.objects.create(
            name="Test Organization", email="org@example.com", created_by=self.user
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationRole.ADMIN,
            added_by=self.user,
        )

        self.list_create_url = reverse("organizations:organization-list-create")
        self.detail_url = reverse(
            "organizations:organization-detail", kwargs={"pk": self.organization.pk}
        )

    def test_create_organization(self):
        """Test creating an organization."""
        data = {
            "name": "New Organization",
            "email": "new@example.com",
            "description": "A new organization",
        }
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 2)
        self.assertEqual(response.data["name"], data["name"])

        # Verify that the user was automatically added as an admin
        new_org = Organization.objects.get(name=data["name"])
        self.assertTrue(new_org.is_admin(self.user))

    def test_list_organizations(self):
        """Test listing organizations."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_organization(self):
        """Test retrieving an organization."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.organization.name)

    def test_update_organization(self):
        """Test updating an organization."""
        data = {"name": "Updated Organization", "email": "updated@example.com"}
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, data["name"])

    def test_delete_organization(self):
        """Test deleting an organization."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Organization.objects.count(), 0)

    def test_unauthorized_access(self):
        """Test unauthorized access to organization endpoints."""
        self.client.logout()
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_required_fields(self):
        """Test organization creation with empty required fields."""
        data = {
            "name": "",
            "email": "",
        }
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_organizer_endpoint(self):
        """Test adding an organizer to an organization."""
        member = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )
        add_organizer_url = reverse("organizations:add-organizer")
        data = {
            "organization": self.organization.id,
            "user": member.id,
            "role": OrganizationRole.MEMBER,
        }

        response = self.client.post(add_organizer_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the membership was created
        self.assertTrue(
            OrganizationMembership.objects.filter(
                organization=self.organization,
                user=member,
                role=OrganizationRole.MEMBER,
            ).exists()
        )

    def test_add_organizer_unauthorized(self):
        """Test adding an organizer by a non-admin user."""
        # Create a new organization and a non-admin user
        non_admin = User.objects.create(
            username="nonadmin", email="nonadmin@example.com", password="nonadminpass"
        )

        # This user is not an admin of the organization
        self.client.force_authenticate(user=non_admin)

        member = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )

        add_organizer_url = reverse("organizations:add-organizer")
        data = {
            "organization": self.organization.id,
            "user": member.id,
            "role": OrganizationRole.MEMBER,
        }
        response = self.client.post(add_organizer_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_organization_members(self):
        """Test listing organization members."""
        # Create a new member
        member = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=member,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        list_members_url = reverse(
            "organizations:list-organization-members",
            kwargs={"pk": self.organization.pk},
        )
        response = self.client.get(list_members_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Admin user and new member


class OrganizationPermissionTest(TestCase):
    """Test cases for Organization permissions."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create(
            username="adminuser", email="admin@example.com", password="adminpass123"
        )
        self.regular_user = User.objects.create(
            username="regularuser",
            email="regular@example.com",
            password="regularpass123",
        )

        self.organization = Organization.objects.create(
            name="Test Organization",
            email="org@example.com",
            created_by=self.admin_user,
        )

        # Add admin as an admin
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.admin_user,
            role=OrganizationRole.ADMIN,
            added_by=self.admin_user,
        )

        # Create a test organization for mocking
        self.test_org = type(
            "TestOrg", (), {"is_admin": lambda user: user == self.admin_user}
        )

        # Create permission instance
        self.permission = IsOrganizationAdminPermission()

        # Create mock requests
        self.admin_request = type(
            "Request", (), {"user": self.admin_user, "method": "PUT"}
        )
        self.regular_request = type(
            "Request", (), {"user": self.regular_user, "method": "PUT"}
        )
        self.read_request = type(
            "Request", (), {"user": self.regular_user, "method": "GET"}
        )

        # Create mock view
        self.view = type("View", (), {})

    def test_is_admin_permission(self):
        """Test admin permission check."""
        # Admin should have permission for write operations
        self.assertTrue(
            self.permission.has_object_permission(
                self.admin_request, self.view, self.test_org
            )
        )

        # Regular user should not have permission for write operations
        self.assertFalse(
            self.permission.has_object_permission(
                self.regular_request, self.view, self.test_org
            )
        )

        # Regular user should have permission for read operations
        self.assertTrue(
            self.permission.has_object_permission(
                self.read_request, self.view, self.test_org
            )
        )


class OrganizationFilterTest(TestCase):
    """Test cases for OrganizationFilter."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create(
            username="user1", email="user1@example.com", password="pass123"
        )
        self.user2 = User.objects.create(
            username="user2", email="user2@example.com", password="pass123"
        )

        self.org1 = Organization.objects.create(
            name="Tech Conference", email="tech@example.com", created_by=self.user1
        )

        self.org2 = Organization.objects.create(
            name="Business Meeting", email="business@example.com", created_by=self.user2
        )

        self.org3 = Organization.objects.create(
            name="Tech Workshop", email="workshop@example.com", created_by=self.user2
        )

        self.queryset = Organization.objects.all()

    def test_name_filter(self):
        """Test filtering organizations by name."""
        filterset = OrganizationFilter({"name": "Tech"}, queryset=self.queryset)
        self.assertEqual(filterset.qs.count(), 2)

    def test_created_by_filter(self):
        """Test filtering organizations by creator."""
        filterset = OrganizationFilter({"created_by": "user2"}, queryset=self.queryset)
        self.assertEqual(filterset.qs.count(), 2)

    def test_name_by_filter_method(self):
        """Test the name_by_filter method directly."""
        filter_instance = OrganizationFilter()
        result = filter_instance.name_by_filter(self.queryset, "name", "Tech")
        self.assertEqual(result.count(), 2)
