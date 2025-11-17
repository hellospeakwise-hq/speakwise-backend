"""custom permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import Organization


class IsOrganizer(BasePermission):
    """custom organizer permission."""

    def has_permission(self, request, view):
        """Check if user is organizer."""
        user = Organization.objects.filter(members=request.user).first()
        return bool(self.user and request.user.is_authenticated and user.is_organizer)


class IsAdminOrOrganizer(BasePermission):
    """custom admin or organizer permission."""

    def has_permission(self, request, view):
        """Check if user is admin or organizer."""
        user = Organization.objects.filter(members=request.user).first()

        return bool(
            user and request.user.is_authenticated and (user.is_organizer_or_admin)
        )


class IsSpeaker(BasePermission):
    """custom speaker permission."""

    def has_permission(self, request, view):
        """Check if user is speaker."""
        user = Organization.objects.filter(members=request.user).first()
        return bool(user and request.user.is_authenticated and user.is_speaker)
