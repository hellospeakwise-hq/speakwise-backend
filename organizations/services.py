"""Business logic for the organizations app."""

from django.db import transaction

from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
from users.models import User


@transaction.atomic
def create_organization_with_admin(data: dict, user: User) -> Organization:
    """Create an organization and add the creator as an admin member.

    Args:
        data: Validated organization data.
        user: The user creating the organization.

    Returns:
        The created Organization instance.
    """
    data["created_by"] = user
    organization = Organization.objects.create(**data)

    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationRole.ADMIN,
        added_by=user,
    )

    return organization
