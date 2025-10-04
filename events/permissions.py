"""Event permissions module."""

from rest_framework import permissions


class EventPermission(permissions.BasePermission):
    """Custom permission to only allow users with event management rights."""

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to manage the event."""
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow GET, HEAD, OPTIONS requests for any user

        memberships = getattr(request.user, "organization_memberships", None)
        return memberships.filter(
            user=request.user,
            is_active=True,
            organization=obj.organization,
            can_manage_events=True,
        ).exists()
