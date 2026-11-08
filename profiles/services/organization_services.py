"""Domain services for organization ownership."""

from django.conf import settings

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


def has_reached_organization_limit(user) -> bool:
    """Return True when the user already owns as many organizations as allowed."""
    owned_count = OrganizationProfile.objects.filter(owner=user).count()
    return owned_count >= get_organization_limit(user)
