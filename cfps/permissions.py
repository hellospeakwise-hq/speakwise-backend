"""CFP permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsEventOrganizer(BasePermission):
    """Check if the request user is an admin or organizer of the event's organization."""

    def has_object_permission(self, request, view, obj):
        """Return True if the user is an organizer of the event."""
        from events.models import Event

        event = obj if isinstance(obj, Event) else obj.event
        return OrganizationMembership.objects.filter(
            organization=event.organizer,
            user=request.user,
            role__in=["ADMIN", "ORGANIZER"],
        ).exists()
