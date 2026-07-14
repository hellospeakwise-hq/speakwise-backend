"""events utils."""

from django.http import Http404

from organizations.models import Organization, OrganizationMembership


def create_event_payload(request):
    """Create event payload."""
    try:
        user = request.user
        membership = OrganizationMembership.objects.filter(user=user).first()
        if not membership:
            raise Http404("User is not a member of any organization.")
        if membership.is_admins() or membership.is_organizers():
            organization = membership.organization
        else:
            raise Http404("User does not have permission to create an event.")
    except Organization.DoesNotExist as err:
        raise Http404("User does not belong to any organization.") from err

    payload = request.data.copy()
    payload["organizer"] = organization.id
    return payload
