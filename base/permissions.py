"""custom permissions."""

from rest_framework.permissions import BasePermission


class IsOrganizer(BasePermission):
    """custom organizer permission."""

    def has_permission(self, request, view):
        """Check if user is organizer."""
        return bool(
            request.user and request.user.is_authenticated and request.user.is_organizer
        )


class IsAdminOrOrganizer(BasePermission):
    """custom admin or organizer permission."""

    def has_permission(self, request, view):
        """Check if user is admin or organizer."""
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_organizer_or_admin)
        )


class IsSpeaker(BasePermission):
    """custom speaker permission."""

    def has_permission(self, request, view):
        """Check if user is speaker."""
        return bool(
            request.user and request.user.is_authenticated and request.user.is_speaker
        )
