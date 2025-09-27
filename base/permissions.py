"""custom permissions."""

from rest_framework.permissions import BasePermission


class IsAdminOrOrganizer(BasePermission):
    """custom admin or organizer permission class."""

    def has_permission(self, request, view):
        """Has permission."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_organizer_or_admin", lambda: False)()
