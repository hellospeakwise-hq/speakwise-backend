"""Domain services for organization ownership."""

from django.conf import settings
from django.contrib.auth import get_user_model

from profiles.choices import OrganizationStatusChoices
from profiles.models.organization_models import OrganizationProfile


def get_owned_organizations(user):
    """Return the organizations a user owns, oldest first.

    Oldest-first keeps the order stable, so "the user's first organization"
    always means the one they created earliest. CFPs are joined because every
    serialized organization includes its CFP.
    """
    return (
        OrganizationProfile.objects.filter(owner=user)
        .select_related("cfps")
        .order_by("created_at")
    )


def get_organization_limit(user) -> int:
    """Return how many organizations the given user may own.

    Every user currently gets the same flat cap. This is the single place to
    change when the cap starts depending on the user's subscription plan.
    """
    return settings.MAX_ORGANIZATIONS_PER_USER


def lock_organization_owner(user):
    """Lock the user's row until the surrounding transaction ends.

    Concurrent organization creates by the same user would otherwise both pass
    the limit check before either saves. Taking this lock before counting
    serialises them, so the second request sees the first one's organization.
    Must be called inside ``transaction.atomic``. It is a no-op on SQLite.
    """
    User = get_user_model()
    User.objects.select_for_update().only("pk").get(pk=user.pk)


def has_reached_organization_limit(user) -> bool:
    """Return True when the user already owns as many organizations as allowed.

    Rejected organizations do not count, so an admin rejection never leaves a
    user stuck at the cap. Pending ones do count, to stop users flooding the
    approval queue, and so do inactive ones (approved, then switched off).
    """
    counted_count = (
        OrganizationProfile.objects.filter(owner=user)
        .exclude(status=OrganizationStatusChoices.REJECTED)
        .count()
    )
    return counted_count >= get_organization_limit(user)
