"""Tests for the organizations app."""

from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
from organizations.serializers import (
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
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=admin_user,
            role=OrganizationRole.ADMIN,
            added_by=self.user,
        )

        self.assertTrue(membership.is_admin())

    def test_get_organizers(self):
        """Test getting all active organization members."""
        member_user = User.objects.create(
            username="memberuser", email="member@example.com", password="memberpass123"
        )
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=member_user,
            role=OrganizationRole.MEMBER,
            added_by=self.user,
        )

        self.assertTrue(membership.is_member())

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
        serializer = OrganizationMembershipSerializer(data=self.membership_data)
        self.assertTrue(serializer.is_valid())

        membership = serializer.save()
        self.assertEqual(
            membership.organization.id, self.membership_data["organization"]
        )
        self.assertEqual(membership.user.id, self.membership_data["user"])
        self.assertEqual(membership.role, self.membership_data["role"])

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
        data_with_readonly = self.membership_data.copy()
        data_with_readonly["created_at"] = "2023-01-01T00:00:00Z"
        data_with_readonly["updated_at"] = "2023-01-01T00:00:00Z"

        serializer = OrganizationMembershipSerializer(data=data_with_readonly)
        self.assertTrue(serializer.is_valid())

        membership = serializer.save()
        self.assertNotEqual(
            membership.created_at.isoformat(), "2023-01-01T00:00:00+00:00"
        )
        self.assertNotEqual(
            membership.updated_at.isoformat(), "2023-01-01T00:00:00+00:00"
        )


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
