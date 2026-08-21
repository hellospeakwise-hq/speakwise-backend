"""custom users' permissions."""

from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """Permission class to check if the user is a superuser."""

    def has_permission(self, request, view):
        """Check if the user is authenticated and is a superuser."""
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user is a superuser."""
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )
