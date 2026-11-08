"""Custom permissions for the profiles app."""

from rest_framework.permissions import BasePermission


class IsOrganizationOwnerOrSuperUser(BasePermission):
    """Allow changes to an organization only by its owner or a superuser.

    Object-level only: views must call ``check_object_permissions`` after
    loading the organization. Ownerless organizations (``owner`` is null)
    can only be changed by superusers.
    """

    message = "You do not have permission to modify this organization."

    def has_object_permission(self, request, view, obj):
        """Return True when the requester owns the organization or is a superuser."""
        user = request.user
        if user.is_superuser:
            return True
        return obj.owner_id is not None and obj.owner_id == user.id
