"""custom users permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the organization."""

    def has_object_permission(self, request, view, obj):
        """Check if the user has admin permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = obj
            if hasattr(obj, "organizer"):
                organization = obj.organizer

            return OrganizationMembership.objects.filter(
                organization=organization, user=request.user, role="ADMIN"
            ).exists()
        return False


class IsOrganizationMember(BasePermission):
    """Permission class to check if the user is a member of the organization."""

    def has_object_permission(self, request, view, obj):
        """Check if the user has member permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = obj
            if hasattr(obj, "organizer"):
                organization = obj.organizer

            return OrganizationMembership.objects.filter(
                organization=organization, user=request.user, is_active=True
            ).exists()
        return False


class IsOrganizationOrganizer(BasePermission):
    """Permission class to check if the user is an organizer of the organization."""

    def has_object_permission(self, request, view, obj):
        """Check if the user has organizer permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = obj
            if hasattr(obj, "organizer"):
                organization = obj.organizer

            return OrganizationMembership.objects.filter(
                organization=organization, user=request.user, role="ORGANIZER"
            ).exists()
        return False


class IsOrganizationAdminOrOrganizer(BasePermission):
    """Permission class to check if the user is an admin or organizer of the organization."""

    def has_object_permission(self, request, view, obj):
        """Check if the user has admin or organizer permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = obj
            if hasattr(obj, "organizer"):
                organization = obj.organizer

            return OrganizationMembership.objects.filter(
                organization=organization,
                user=request.user,
                role__in=["ADMIN", "ORGANIZER"],
            ).exists()
        return False
