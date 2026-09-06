"""Organization profile, CFP, serializer, and view tests."""

import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from profiles.choices import OrganizationStatusChoices
from profiles.models import OrganizationProfile
from profiles.models.organization_models import OrganizationCFP
from profiles.serializers.organization_serializers import (
    OrganizationCFPSerializer,
    OrganizationProfileSerializer,
)


class OrganizationCFPModelTests(TestCase):
    """Tests for the OrganizationCFP model."""

    def setUp(self):
        """Create a closed and an open CFP."""
        now = timezone.now()
        self.open_cfp = OrganizationCFP.objects.create(
            url="https://example.com/cfp",
            description="Join us!",
            open_at=now - timedelta(days=1),
            close_at=now + timedelta(days=5),
        )
        self.closed_cfp = OrganizationCFP.objects.create(
            url="https://example.com/cfp-closed",
            description="Too late.",
            open_at=now - timedelta(days=10),
            close_at=now - timedelta(days=1),
        )

    def test_organization_cfp_creation(self):
        """All CFP fields are persisted correctly."""
        self.assertEqual(self.open_cfp.url, "https://example.com/cfp")
        self.assertEqual(self.open_cfp.description, "Join us!")
        self.assertIsNotNone(self.open_cfp.open_at)
        self.assertIsNotNone(self.open_cfp.close_at)

    def test_organization_cfp_str_returns_url(self):
        """__str__ returns the CFP url."""
        self.assertEqual(str(self.open_cfp), "https://example.com/cfp")


class OrganizationProfileModelTests(TestCase):
    """Tests for the OrganizationProfile model."""

    def setUp(self):
        """Create an organization and open/closed CFPs."""
        now = timezone.now()
        self.organization = OrganizationProfile.objects.create(
            name="Acme Corp",
            description="A test organization",
            website="https://acme.example.com",
            contact_email="hello@acme.example.com",
        )
        self.open_cfp = OrganizationCFP.objects.create(
            url="https://acme.example.com/cfp",
            open_at=now - timedelta(days=1),
            close_at=now + timedelta(days=5),
        )
        self.closed_cfp = OrganizationCFP.objects.create(
            url="https://acme.example.com/cfp-closed",
            open_at=now - timedelta(days=10),
            close_at=now - timedelta(days=1),
        )

    def test_organization_profile_creation(self):
        """All organization fields are persisted correctly."""
        self.assertEqual(self.organization.name, "Acme Corp")
        self.assertEqual(self.organization.description, "A test organization")
        self.assertEqual(self.organization.website, "https://acme.example.com")
        self.assertEqual(self.organization.contact_email, "hello@acme.example.com")

    def test_organization_str_returns_name(self):
        """__str__ returns the organization name."""
        self.assertEqual(str(self.organization), "Acme Corp")

    def test_organization_id_is_uuid(self):
        """The primary key is a UUID."""
        self.assertIsInstance(self.organization.id, uuid.UUID)

    def test_organization_name_is_unique(self):
        """Creating a second organization with the same name is rejected."""
        with self.assertRaises(IntegrityError):
            OrganizationProfile.objects.create(name="Acme Corp")

    def test_organization_timestamps_are_set(self):
        """created_at and updated_at are populated on creation."""
        self.assertIsNotNone(self.organization.created_at)
        self.assertIsNotNone(self.organization.updated_at)

    def test_cfp_is_nulled_when_cfp_deleted(self):
        """Deleting the linked CFP sets the cfps FK to NULL (SET_NULL)."""
        self.organization.cfps = self.open_cfp
        self.organization.save()
        self.open_cfp.delete()
        self.organization.refresh_from_db()
        self.assertIsNone(self.organization.cfps)

    def test_get_open_cfps_returns_open_cfp(self):
        """get_open_cfps returns the linked CFP still open."""
        self.organization.cfps = self.open_cfp
        self.organization.save()
        self.assertIn(self.open_cfp, list(self.organization.get_open_cfps()))

    def test_get_closed_cfps_returns_closed_cfp(self):
        """get_closed_cfps returns the linked CFP whose close date passed."""
        self.organization.cfps = self.closed_cfp
        self.organization.save()
        self.assertIn(self.closed_cfp, list(self.organization.get_closed_cfps()))

    def test_get_open_cfps_excludes_closed_cfp(self):
        """get_open_cfps is empty when the linked CFP is closed."""
        self.organization.cfps = self.closed_cfp
        self.organization.save()
        self.assertEqual(list(self.organization.get_open_cfps()), [])
        self.assertIn(self.closed_cfp, list(self.organization.get_closed_cfps()))

    def test_get_cfps_empty_when_no_cfp_linked(self):
        """get_open_cfps/get_closed_cfps are empty with no linked CFP."""
        self.assertEqual(list(self.organization.get_open_cfps()), [])
        self.assertEqual(list(self.organization.get_closed_cfps()), [])


class OrganizationCFPSerializerTests(TestCase):
    """Tests for the OrganizationCFPSerializer."""

    def test_serializer_exposes_cfp_fields(self):
        """The serializer exposes url, description, open_at, and close_at."""
        cfp = OrganizationCFP.objects.create(
            url="https://example.com/cfp",
            description="Join us!",
        )
        serializer = OrganizationCFPSerializer(instance=cfp)
        self.assertEqual(
            set(serializer.data.keys()),
            {"url", "description", "open_at", "close_at"},
        )
        self.assertEqual(serializer.data["url"], "https://example.com/cfp")
        self.assertEqual(serializer.data["description"], "Join us!")


class OrganizationProfileSerializerTests(TestCase):
    """Tests for the OrganizationProfileSerializer."""

    def setUp(self):
        """Create an organization."""
        self.organization = OrganizationProfile.objects.create(
            name="Acme Corp",
            description="A test organization",
            website="https://acme.example.com",
            contact_email="hello@acme.example.com",
        )

    def test_serializer_exposes_expected_fields(self):
        """The serializer exposes all public organization fields."""
        serializer = OrganizationProfileSerializer(instance=self.organization)
        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "owner",
                "name",
                "description",
                "website",
                "branding",
                "contact_email",
                "status",
                "cfps",
            },
        )

    def test_serializer_id_is_stringified_uuid(self):
        """The id is serialized as the stringified UUID."""
        serializer = OrganizationProfileSerializer(instance=self.organization)
        self.assertEqual(serializer.data["id"], str(self.organization.id))

    def test_cfps_is_none_when_no_cfp_linked(self):
        """Cfps serializes to None when the organization has no linked CFP."""
        serializer = OrganizationProfileSerializer(instance=self.organization)
        self.assertIsNone(serializer.data["cfps"])

    def test_cfps_is_dict_when_cfp_linked(self):
        """Cfps serializes to the linked CFP object when set."""
        cfp = OrganizationCFP.objects.create(url="https://acme.example.com/cfp")
        self.organization.cfps = cfp
        self.organization.save()

        serializer = OrganizationProfileSerializer(instance=self.organization)
        self.assertEqual(serializer.data["cfps"]["url"], "https://acme.example.com/cfp")

    def test_name_is_required(self):
        """Serialization without a name is invalid."""
        serializer = OrganizationProfileSerializer(data={"description": "No name"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_duplicate_name_is_rejected(self):
        """Serialization with an existing name is invalid."""
        serializer = OrganizationProfileSerializer(data={"name": "Acme Corp"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_invalid_website_is_rejected(self):
        """Serialization with a malformed website URL is invalid."""
        serializer = OrganizationProfileSerializer(
            data={"name": "Another Org", "website": "not-a-url"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("website", serializer.errors)

    def test_valid_organization_serializes(self):
        """A valid payload serializes successfully."""
        serializer = OrganizationProfileSerializer(
            data={
                "name": "Beta Corp",
                "description": "Another org",
                "website": "https://beta.example.com",
                "contact_email": "beta@example.com",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class OrganizationProfileListCreateViewTests(APITestCase):
    """Tests for list and create endpoints."""

    def setUp(self):
        """Create an authenticated client and two organizations."""
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username="orglistuser",
            email="orglist@example.com",
            password="testpass123",
        )
        self.org_a = OrganizationProfile.objects.create(name="Alpha Org")
        self.org_b = OrganizationProfile.objects.create(name="Beta Org")
        self.list_url = reverse("organization:organization-list-create")

    def test_unauthenticated_list_returns_200(self):
        """Listing organizations is public and requires no authentication."""
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_create_returns_401(self):
        """Creating an organization requires authentication."""
        res = self.client.post(self.list_url, {"name": "Bogus"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_all_organizations(self):
        """The list endpoint returns every organization."""
        self.client.force_authenticate(self.user)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = {org["name"] for org in res.data}
        self.assertIn("Alpha Org", names)
        self.assertIn("Beta Org", names)

    def test_list_is_empty_when_no_organizations(self):
        """The list endpoint returns an empty list when none exist."""
        OrganizationProfile.objects.all().delete()
        self.client.force_authenticate(self.user)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_create_organization_returns_201(self):
        """A valid payload creates the organization and returns it."""
        self.client.force_authenticate(self.user)
        payload = {
            "name": "Gamma Org",
            "description": "Brand new",
            "website": "https://gamma.example.com",
            "contact_email": "gamma@example.com",
        }
        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["name"], "Gamma Org")
        self.assertEqual(res.data["website"], "https://gamma.example.com")
        self.assertTrue(OrganizationProfile.objects.filter(name="Gamma Org").exists())

    def test_create_sets_owner_to_request_user(self):
        """The authenticated user who creates the organization becomes its owner."""
        self.client.force_authenticate(self.user)
        res = self.client.post(self.list_url, {"name": "Owner Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        organization = OrganizationProfile.objects.get(name="Owner Org")
        self.assertEqual(organization.owner, self.user)
        self.assertEqual(res.data["owner"], self.user.id)

    def test_create_ignores_client_supplied_owner(self):
        """The owner field cannot be set by the client; it is always the current user."""
        other_user = get_user_model().objects.create(
            username="orgotheruser",
            email="orgother@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)
        res = self.client.post(
            self.list_url,
            {"name": "Sneaky Org", "owner": str(other_user.id)},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        organization = OrganizationProfile.objects.get(name="Sneaky Org")
        self.assertEqual(organization.owner, self.user)
        self.assertNotEqual(organization.owner, other_user)

    def test_create_duplicate_name_returns_400(self):
        """Creating an organization with a duplicate name is rejected."""
        self.client.force_authenticate(self.user)
        res = self.client.post(self.list_url, {"name": "Alpha Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", res.data)

    def test_create_missing_name_returns_400(self):
        """Creating an organization without a name is rejected."""
        self.client.force_authenticate(self.user)
        res = self.client.post(self.list_url, {"description": "No name"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", res.data)

    def test_create_invalid_website_returns_400(self):
        """Creating an organization with a malformed website is rejected."""
        self.client.force_authenticate(self.user)
        res = self.client.post(
            self.list_url, {"name": "Delta Org", "website": "not-a-url"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", res.data)


class OrganizationProfileDetailViewTests(APITestCase):
    """Tests for retrieve, update, and delete endpoints."""

    def setUp(self):
        """Create an authenticated client and one organization."""
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username="orgdetailuser",
            email="orgdetail@example.com",
            password="testpass123",
        )
        self.organization = OrganizationProfile.objects.create(
            name="Alpha Org",
            description="Original description",
        )
        self.detail_url = reverse(
            "organization:organization-detail", kwargs={"pk": self.organization.id}
        )

    def test_unauthenticated_get_returns_401(self):
        """Retrieving an organization requires authentication."""
        res = self.client.get(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_put_returns_401(self):
        """Updating an organization requires authentication."""
        res = self.client.put(self.detail_url, {"name": "Hack"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_returns_401(self):
        """Deleting an organization requires authentication."""
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_organization(self):
        """The detail endpoint returns the requested organization."""
        self.client.force_authenticate(self.user)
        res = self.client.get(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Alpha Org")
        self.assertEqual(res.data["id"], str(self.organization.id))

    def test_get_unknown_pk_returns_404(self):
        """Retrieving an unknown organization returns 404."""
        self.client.force_authenticate(self.user)
        url = reverse(
            "organization:organization-detail",
            kwargs={"pk": uuid.uuid4()},
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_updates_organization(self):
        """PUT updates the organization and returns the updated object."""
        self.client.force_authenticate(self.user)
        payload = {
            "name": "Alpha Org Updated",
            "description": "Updated description",
            "website": "https://alpha.example.com",
            "contact_email": "new@example.com",
        }
        res = self.client.put(self.detail_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Alpha Org Updated")
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "Alpha Org Updated")
        self.assertEqual(self.organization.website, "https://alpha.example.com")

    def test_put_duplicate_name_returns_400(self):
        """PUT with a name already used by another organization is rejected."""
        OrganizationProfile.objects.create(name="Other Org")
        self.client.force_authenticate(self.user)
        res = self.client.put(self.detail_url, {"name": "Other Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", res.data)

    def test_put_invalid_website_returns_400(self):
        """PUT with a malformed website is rejected."""
        self.client.force_authenticate(self.user)
        res = self.client.put(
            self.detail_url,
            {"name": "Alpha Org", "website": "not-a-url"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", res.data)

    def test_put_unknown_pk_returns_404(self):
        """PUT on an unknown organization returns 404."""
        self.client.force_authenticate(self.user)
        url = reverse(
            "organization:organization-detail",
            kwargs={"pk": uuid.uuid4()},
        )
        res = self.client.put(url, {"name": "Ghost"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_removes_organization(self):
        """DELETE removes the organization and returns 204."""
        self.client.force_authenticate(self.user)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            OrganizationProfile.objects.filter(id=self.organization.id).exists()
        )

    def test_delete_unknown_pk_returns_404(self):
        """DELETE on an unknown organization returns 404."""
        self.client.force_authenticate(self.user)
        url = reverse(
            "organization:organization-detail",
            kwargs={"pk": uuid.uuid4()},
        )
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class OrganizationSignalTests(TestCase):
    """Tests for the organization signals."""

    def setUp(self):
        """Set up the test client."""
        self.organization = OrganizationProfile.objects.create(
            name="Test Org",
            status=OrganizationStatusChoices.PENDING,
            contact_email="test@example.com",
        )

    def test_status_update_from_pending_to_active_sends_email(self):
        """Updating status from pending to active should send an email."""
        self.organization.status = OrganizationStatusChoices.ACTIVE
        self.organization.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
        self.assertIn("Test Org", mail.outbox[0].subject)

    def test_status_update_from_pending_to_rejected_sends_email(self):
        """Updating status from pending to rejected should send an email."""
        self.organization.status = OrganizationStatusChoices.REJECTED
        self.organization.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
        self.assertIn("Test Org", mail.outbox[0].subject)

    def test_status_update_from_active_to_rejected_does_not_send_email(self):
        """Updating status from active to rejected should NOT send an email."""
        self.organization.status = OrganizationStatusChoices.ACTIVE
        self.organization.save()

        # Reset outbox
        mail.outbox = []

        self.organization.status = OrganizationStatusChoices.REJECTED
        self.organization.save()
        self.assertEqual(len(mail.outbox), 0)
