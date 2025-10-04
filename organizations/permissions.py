"""Permissions for organization views."""

from rest_framework import permissions


class IsOrganizationAdminPermission(permissions.BasePermission):
    """Custom permission to check if user is admin of the organization."""

    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the specific organization."""
        # For safe methods (GET, HEAD, OPTIONS), allow if user is a member
        if request.method in permissions.SAFE_METHODS:
            return obj.is_member(request.user)

        # For unsafe methods (PUT, PATCH, DELETE), require admin access
        return obj.is_admin(request.user)
