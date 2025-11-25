"""custom users permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the organization."""

    def has_permission(self, request, view):
        """Check if the user has admin permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.get(user=request.user)
                return membership.is_admins()
            except OrganizationMembership.DoesNotExist:
                return False
        return False


class IsOrganizationMember(BasePermission):
    """Permission class to check if the user is a member of the organization."""

    def has_permission(self, request, view):
        """Check if the user has member permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.get(user=request.user)
                return membership.is_active
            except OrganizationMembership.DoesNotExist:
                return False
        return False


class IsOrganizationOrganizer(BasePermission):
    """Permission class to check if the user is an organizer of the organization."""

    def has_permission(self, request, view):
        """Check if the user has organizer permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.get(user=request.user)
                return membership.is_organizers()
            except OrganizationMembership.DoesNotExist:
                return False
        return False
