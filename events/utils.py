"""events utils."""

from django.http import Http404

from organizations.models import Organization, OrganizationMembership


def create_event_payload(request):
    """Create event payload."""
    print(request.data)
    try:
        user = request.user
        membership = OrganizationMembership.objects.get(user=user)
        if membership.is_admins() or membership.is_organizers():
            organization = membership.organization
        else:
            raise Http404("User does not have permission to create an event.")
    except Organization.DoesNotExist as err:
        raise Http404("User does not belong to any organization.") from err
    except OrganizationMembership.DoesNotExist as err:
        raise Http404("User is not a member of the organization.") from err

    request.data.update(
        {
            "organizer": organization.id,
        }
    )
    payload = request.data
    return payload
