"""Custom permissions for organization-related views."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from organizations.models import Organization


class IsOrganizationAdminPermission(BasePermission):
    """Custom permission to check if the user is an admin of the organization."""

    def has_permission(self, request, view):
        """Check if the user has permission for the view."""
        if request.method in SAFE_METHODS:
            return True

        # For create actions, check organization in data
        if request.method == "POST":
            organization_id = request.data.get("organization")
            if organization_id:
                try:
                    organization = Organization.objects.get(id=organization_id)
                    return organization.is_admin(request.user)
                except Organization.DoesNotExist:
                    return False
        return True  # Default to allowing, let has_object_permission handle it

    def has_object_permission(self, request, view, obj):
        """Check if the user is an admin of the organization."""
        if request.method in SAFE_METHODS:
            return True  # Allow read-only access for any authenticated user

        # Get the organization from the object
        if hasattr(obj, "organization"):
            organization = obj.organization
        elif hasattr(obj, "is_admin"):
            organization = obj
        else:
            return False

        return organization.is_admin(request.user)
