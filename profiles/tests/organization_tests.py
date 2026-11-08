"""Organization profile, CFP, serializer, and view tests."""

import uuid
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from profiles.choices import OrganizationStatusChoices
from profiles.models import OrganizationProfile, SpeakerProfile
from profiles.models.organization_models import OrganizationCFP
from profiles.permissions import IsOrganizationOwnerOrSuperUser
from profiles.serializers.organization_serializers import (
    OrganizationCFPSerializer,
    OrganizationProfileSerializer,
)
from profiles.services.organization_services import (
    get_organization_limit,
    get_owned_organizations,
    has_reached_organization_limit,
    lock_organization_owner,
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
                "admin_notes",
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
            is_email_verified=True,
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
        names = {org["name"] for org in res.data["results"]}
        self.assertIn("Alpha Org", names)
        self.assertIn("Beta Org", names)

    def test_list_is_empty_when_no_organizations(self):
        """The list endpoint returns an empty list when none exist."""
        OrganizationProfile.objects.all().delete()
        self.client.force_authenticate(self.user)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], [])

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
            is_email_verified=True,
        )
        self.other_user = get_user_model().objects.create(
            username="orgdetailother",
            email="orgdetailother@example.com",
            password="testpass123",
            is_email_verified=True,
        )
        self.superuser = get_user_model().objects.create_superuser(
            username="orgdetailadmin",
            email="orgdetailadmin@example.com",
            password="testpass123",
            is_email_verified=True,
        )
        self.organization = OrganizationProfile.objects.create(
            name="Alpha Org",
            description="Original description",
            owner=self.user,
        )
        self.detail_url = reverse(
            "organization:organization-detail", kwargs={"pk": self.organization.id}
        )

    def test_unauthenticated_get_returns_200(self):
        """Retrieving an organization is public."""
        res = self.client.get(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

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

    def test_non_owner_put_returns_403_and_leaves_organization_unchanged(self):
        """A verified user who does not own the organization cannot update it."""
        self.client.force_authenticate(self.other_user)
        res = self.client.put(self.detail_url, {"name": "Hijacked"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            res.data["detail"],
            "You do not have permission to modify this organization.",
        )
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "Alpha Org")
        self.assertEqual(self.organization.owner, self.user)

    def test_non_owner_delete_returns_403_and_keeps_organization(self):
        """A verified user who does not own the organization cannot delete it."""
        self.client.force_authenticate(self.other_user)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            OrganizationProfile.objects.filter(id=self.organization.id).exists()
        )

    def test_superuser_can_update_organization_they_do_not_own(self):
        """Superusers may update any organization; ownership is unchanged."""
        self.client.force_authenticate(self.superuser)
        res = self.client.put(self.detail_url, {"name": "Admin Fixed"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "Admin Fixed")
        self.assertEqual(self.organization.owner, self.user)

    def test_superuser_can_delete_organization_they_do_not_own(self):
        """Superusers may delete any organization."""
        self.client.force_authenticate(self.superuser)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            OrganizationProfile.objects.filter(id=self.organization.id).exists()
        )

    def test_ownerless_organization_cannot_be_changed_by_regular_user(self):
        """An organization with no owner is editable only by superusers."""
        ownerless = OrganizationProfile.objects.create(name="Ownerless Org")
        url = reverse("organization:organization-detail", kwargs={"pk": ownerless.id})
        self.client.force_authenticate(self.user)
        put_res = self.client.put(url, {"name": "Claimed"}, format="json")
        delete_res = self.client.delete(url)
        self.assertEqual(put_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_res.status_code, status.HTTP_403_FORBIDDEN)
        ownerless.refresh_from_db()
        self.assertEqual(ownerless.name, "Ownerless Org")

    def test_unverified_owner_put_returns_403(self):
        """Owners must still have a verified email address to make changes."""
        self.user.is_email_verified = False
        self.user.save(update_fields=["is_email_verified"])
        self.client.force_authenticate(self.user)
        res = self.client.put(self.detail_url, {"name": "Unverified"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            res.data["detail"],
            "Email verification is required to perform this action.",
        )
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "Alpha Org")

    def test_unverified_owner_delete_returns_403_and_keeps_organization(self):
        """Unverified owners cannot delete, and see the email message."""
        self.user.is_email_verified = False
        self.user.save(update_fields=["is_email_verified"])
        self.client.force_authenticate(self.user)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            res.data["detail"],
            "Email verification is required to perform this action.",
        )
        self.assertTrue(
            OrganizationProfile.objects.filter(id=self.organization.id).exists()
        )

    def test_unverified_superuser_put_returns_403(self):
        """Superusers also need a verified email address to make changes."""
        self.superuser.is_email_verified = False
        self.superuser.save(update_fields=["is_email_verified"])
        self.client.force_authenticate(self.superuser)
        res = self.client.put(self.detail_url, {"name": "Admin Fixed"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "Alpha Org")

    def test_non_owner_can_still_retrieve_organization(self):
        """Reading an organization stays public to non-owners."""
        self.client.force_authenticate(self.other_user)
        res = self.client.get(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Alpha Org")


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


@override_settings(MAX_ORGANIZATIONS_PER_USER=3)
class OrganizationOwnershipLimitTests(APITestCase):
    """Tests for who may create organizations and how many they may own."""

    def setUp(self):
        """Set up an authenticated client and a user with no profile."""
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create(
            username="orgrestrict",
            email="orgrestrict@example.com",
            password="testpass123",
            is_email_verified=True,
        )
        self.other_user = User.objects.create(
            username="orgrestrictother",
            email="orgrestrictother@example.com",
            password="testpass123",
            is_email_verified=True,
        )
        self.client.force_authenticate(self.user)
        self.list_url = reverse("organizations:organization-list-create")

    def _own(self, count, owner=None):
        """Create ``count`` organizations owned by ``owner`` (default: self.user)."""
        owner = owner or self.user
        for index in range(count):
            OrganizationProfile.objects.create(
                name=f"{owner.username} Org {index}", owner=owner
            )

    def test_speaker_can_create_organization(self):
        """A user with a speaker profile can also own an organization."""
        SpeakerProfile.objects.create(user_account=self.user, organization="Acme")
        res = self.client.post(self.list_url, {"name": "Speaker Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        organization = OrganizationProfile.objects.get(name="Speaker Org")
        self.assertEqual(organization.owner, self.user)
        self.assertEqual(organization.status, OrganizationStatusChoices.PENDING)
        self.assertTrue(SpeakerProfile.objects.filter(user_account=self.user).exists())

    def test_user_can_create_organizations_up_to_the_limit(self):
        """A user owning fewer than the limit can create another organization."""
        self._own(2)
        res = self.client.post(self.list_url, {"name": "Third Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrganizationProfile.objects.filter(owner=self.user).count(), 3)

    def test_organization_beyond_the_limit_is_rejected(self):
        """Creating an organization past the limit returns 400 and creates nothing."""
        self._own(3)
        res = self.client.post(self.list_url, {"name": "Fourth Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(res.data["detail"]),
            "You have reached the maximum number of organizations you can own (3).",
        )
        self.assertFalse(OrganizationProfile.objects.filter(name="Fourth Org").exists())
        self.assertEqual(OrganizationProfile.objects.filter(owner=self.user).count(), 3)

    @override_settings(MAX_ORGANIZATIONS_PER_USER=1)
    def test_limit_follows_the_configured_setting(self):
        """The cap comes from MAX_ORGANIZATIONS_PER_USER, not a hardcoded number."""
        self._own(1)
        res = self.client.post(self.list_url, {"name": "Second Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(res.data["detail"]),
            "You have reached the maximum number of organizations you can own (1).",
        )

    def test_other_users_organizations_do_not_count_toward_the_limit(self):
        """Only organizations the requester owns count toward their cap."""
        self._own(3, owner=self.other_user)
        res = self.client.post(self.list_url, {"name": "My Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_owner_is_locked_before_the_limit_is_checked(self):
        """The owner row lock must be taken before counting, or races slip through."""
        calls = mock.Mock()
        calls.has_reached.return_value = False
        with (
            mock.patch(
                "profiles.serializers.organization_serializers.lock_organization_owner",
                calls.lock,
            ),
            mock.patch(
                "profiles.serializers.organization_serializers."
                "has_reached_organization_limit",
                calls.has_reached,
            ),
        ):
            res = self.client.post(self.list_url, {"name": "Locked Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            calls.mock_calls,
            [mock.call.lock(self.user), mock.call.has_reached(self.user)],
        )

    def test_limit_check_runs_inside_a_transaction(self):
        """Locking only works inside a transaction, so create must open one."""
        observed = {}

        def record_atomic_block(user):
            observed["in_atomic_block"] = connection.in_atomic_block

        with mock.patch(
            "profiles.serializers.organization_serializers.lock_organization_owner",
            side_effect=record_atomic_block,
        ):
            self.client.post(self.list_url, {"name": "Atomic Org"}, format="json")
        self.assertTrue(observed["in_atomic_block"])

    def test_user_with_only_rejected_organizations_can_create_another(self):
        """Rejected organizations never block a user from creating a new one."""
        for index in range(3):
            OrganizationProfile.objects.create(
                name=f"Rejected Org {index}",
                owner=self.user,
                status=OrganizationStatusChoices.REJECTED,
            )
        res = self.client.post(self.list_url, {"name": "Fresh Org"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], OrganizationStatusChoices.PENDING)
        self.assertEqual(OrganizationProfile.objects.filter(owner=self.user).count(), 4)

    def test_deleting_an_organization_frees_a_slot(self):
        """After deleting one of their organizations, a user at the cap can create again."""
        self._own(3)
        OrganizationProfile.objects.filter(owner=self.user).first().delete()
        res = self.client.post(
            self.list_url, {"name": "Replacement Org"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


@override_settings(MAX_ORGANIZATIONS_PER_USER=3)
class OrganizationServiceTests(TestCase):
    """Tests for the organization ownership service functions."""

    def setUp(self):
        """Create two users."""
        User = get_user_model()
        self.user = User.objects.create(
            username="orgservice", email="orgservice@example.com"
        )
        self.other_user = User.objects.create(
            username="orgserviceother", email="orgserviceother@example.com"
        )

    def test_get_organization_limit_returns_configured_setting(self):
        """The limit is read from settings."""
        self.assertEqual(get_organization_limit(self.user), 3)
        with self.settings(MAX_ORGANIZATIONS_PER_USER=7):
            self.assertEqual(get_organization_limit(self.user), 7)

    def test_has_reached_limit_is_false_below_the_cap(self):
        """A user owning fewer organizations than the cap has not reached it."""
        OrganizationProfile.objects.create(name="One", owner=self.user)
        OrganizationProfile.objects.create(name="Two", owner=self.user)
        self.assertFalse(has_reached_organization_limit(self.user))

    def test_has_reached_limit_is_true_at_the_cap(self):
        """A user owning exactly the cap has reached it."""
        for name in ("One", "Two", "Three"):
            OrganizationProfile.objects.create(name=name, owner=self.user)
        self.assertTrue(has_reached_organization_limit(self.user))

    def _own_with_statuses(self, *statuses):
        """Create one organization owned by self.user per given status."""
        for index, org_status in enumerate(statuses):
            OrganizationProfile.objects.create(
                name=f"Status Org {index}", owner=self.user, status=org_status
            )

    def test_rejected_organizations_do_not_count_toward_the_limit(self):
        """A user whose organizations were all rejected is not at the cap."""
        rejected = OrganizationStatusChoices.REJECTED
        self._own_with_statuses(rejected, rejected, rejected)
        self.assertFalse(has_reached_organization_limit(self.user))

    def test_rejected_organization_frees_its_slot_alongside_counted_ones(self):
        """Two counted organizations plus a rejected one leave room for one more."""
        self._own_with_statuses(
            OrganizationStatusChoices.ACTIVE,
            OrganizationStatusChoices.PENDING,
            OrganizationStatusChoices.REJECTED,
        )
        self.assertFalse(has_reached_organization_limit(self.user))

    def test_pending_organizations_count_toward_the_limit(self):
        """Pending organizations count, so the approval queue cannot be flooded."""
        pending = OrganizationStatusChoices.PENDING
        self._own_with_statuses(pending, pending, pending)
        self.assertTrue(has_reached_organization_limit(self.user))

    def test_active_organizations_count_toward_the_limit(self):
        """Approved organizations count."""
        active = OrganizationStatusChoices.ACTIVE
        self._own_with_statuses(active, active, active)
        self.assertTrue(has_reached_organization_limit(self.user))

    def test_inactive_organizations_count_toward_the_limit(self):
        """Approved-then-deactivated organizations still count."""
        inactive = OrganizationStatusChoices.INACTIVE
        self._own_with_statuses(inactive, inactive, inactive)
        self.assertTrue(has_reached_organization_limit(self.user))

    def test_organizations_with_no_status_count_toward_the_limit(self):
        """A null status (the field allows it) is not treated as rejected."""
        self._own_with_statuses(None, None, None)
        self.assertTrue(has_reached_organization_limit(self.user))

    def test_has_reached_limit_is_false_for_user_with_no_organizations(self):
        """A user with no organizations has not reached the cap."""
        self.assertFalse(has_reached_organization_limit(self.user))

    def test_get_owned_organizations_returns_only_users_orgs_oldest_first(self):
        """Owned organizations are scoped to the user and ordered by creation."""
        newer = OrganizationProfile.objects.create(name="Newer", owner=self.user)
        older = OrganizationProfile.objects.create(name="Older", owner=self.user)
        OrganizationProfile.objects.create(name="Not Mine", owner=self.other_user)
        OrganizationProfile.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )
        OrganizationProfile.objects.filter(pk=newer.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        self.assertEqual(list(get_owned_organizations(self.user)), [older, newer])

    def test_lock_organization_owner_selects_only_the_users_row(self):
        """The lock query targets exactly the given user's row."""
        with transaction.atomic(), CaptureQueriesContext(connection) as queries:
            lock_organization_owner(self.user)
        self.assertEqual(len(queries), 1)
        sql = queries[0]["sql"]
        self.assertIn("users_user", sql)
        self.assertIn(self.user.pk.hex, sql.replace("-", ""))

    def test_get_owned_organizations_is_empty_for_user_without_orgs(self):
        """A user who owns nothing gets an empty queryset."""
        self.assertFalse(get_owned_organizations(self.user).exists())


@override_settings(ADMIN_NOTIFICATION_EMAILS=["admin@example.com"])
class OrganizationEmailNotificationTests(TestCase):
    """Emails sent on organization creation and approval."""

    def test_admin_alerted_on_new_organization(self):
        """Creating a pending organization emails the admins once."""
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            OrganizationProfile.objects.create(name="Notify Org")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("Notify Org", mail.outbox[0].subject)

    def test_organization_emailed_when_approved(self):
        """Approving a pending organization sends a congratulations email."""
        with self.captureOnCommitCallbacks(execute=True):
            org = OrganizationProfile.objects.create(
                name="Approve Org", contact_email="org@example.com"
            )
        mail.outbox.clear()
        org.status = OrganizationStatusChoices.ACTIVE
        org.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["org@example.com"])
        self.assertIn("approved", mail.outbox[0].subject)


class IsOrganizationOwnerOrSuperUserTests(TestCase):
    """Unit tests for the combined email-verified and ownership permission."""

    def setUp(self):
        """Create an owner, a non-owner, a superuser, and one organization."""
        user_model = get_user_model()
        self.owner = user_model.objects.create(
            username="permowner", email="permowner@example.com", is_email_verified=True
        )
        self.other_user = user_model.objects.create(
            username="permother", email="permother@example.com", is_email_verified=True
        )
        self.superuser = user_model.objects.create_superuser(
            username="permadmin",
            email="permadmin@example.com",
            password="testpass123",
            is_email_verified=True,
        )
        self.organization = OrganizationProfile.objects.create(
            name="Perm Org", owner=self.owner
        )
        self.factory = APIRequestFactory()

    def _request_as(self, user):
        """Build a write request authenticated as the given user."""
        request = self.factory.put("/")
        request.user = user
        return request

    def test_has_permission_allows_verified_user(self):
        """Verified users pass the view-level check."""
        permission = IsOrganizationOwnerOrSuperUser()
        self.assertTrue(permission.has_permission(self._request_as(self.owner), None))

    def test_has_permission_denies_unverified_user_with_email_message(self):
        """Unverified users fail the view-level check with the email message."""
        self.owner.is_email_verified = False
        permission = IsOrganizationOwnerOrSuperUser()
        self.assertFalse(permission.has_permission(self._request_as(self.owner), None))
        self.assertEqual(
            permission.message,
            "Email verification is required to perform this action.",
        )

    def test_has_permission_denies_anonymous_user(self):
        """Anonymous users fail the view-level check."""
        permission = IsOrganizationOwnerOrSuperUser()
        request = self._request_as(AnonymousUser())
        self.assertFalse(permission.has_permission(request, None))

    def test_has_object_permission_allows_owner(self):
        """The owner passes the object-level check."""
        permission = IsOrganizationOwnerOrSuperUser()
        request = self._request_as(self.owner)
        self.assertTrue(
            permission.has_object_permission(request, None, self.organization)
        )

    def test_has_object_permission_allows_superuser(self):
        """A superuser passes the object-level check for any organization."""
        permission = IsOrganizationOwnerOrSuperUser()
        request = self._request_as(self.superuser)
        self.assertTrue(
            permission.has_object_permission(request, None, self.organization)
        )

    def test_has_object_permission_denies_non_owner_with_owner_message(self):
        """A non-owner fails the object-level check with the ownership message."""
        permission = IsOrganizationOwnerOrSuperUser()
        request = self._request_as(self.other_user)
        self.assertFalse(
            permission.has_object_permission(request, None, self.organization)
        )
        self.assertEqual(
            permission.message,
            "You do not have permission to modify this organization.",
        )

    def test_has_object_permission_denies_regular_user_on_ownerless_organization(self):
        """Ownerless organizations are closed to every non-superuser."""
        ownerless = OrganizationProfile.objects.create(name="Perm Ownerless")
        permission = IsOrganizationOwnerOrSuperUser()
        request = self._request_as(self.owner)
        self.assertFalse(permission.has_object_permission(request, None, ownerless))
