"""custom users permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the organization."""

    def has_permission(self, request, view):
        """Check if the user has admin permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                return (
                    OrganizationMembership.objects.filter(user=request.user)
                    .first()
                    .is_admin()
                )
            except OrganizationMembership.DoesNotExist:
                return False
        return False


class IsOrganizationMember(BasePermission):
    """Permission class to check if the user is a member of the organization."""

    def has_permission(self, request, view):
        """Check if the user has member permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                return (
                    OrganizationMembership.objects.filter(user=request.user)
                    .first()
                    .is_member()
                )
            except OrganizationMembership.DoesNotExist:
                return False
        return False


class IsOrganizationOrganizer(BasePermission):
    """Permission class to check if the user is an organizer of the organization."""

    def has_permission(self, request, view):
        """Check if the user has organizer permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                return (
                    OrganizationMembership.objects.filter(user=request.user)
                    .first()
                    .is_organizer()
                )
            except OrganizationMembership.DoesNotExist:
                return False
        return False
