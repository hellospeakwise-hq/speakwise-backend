"""custom users permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the organization."""

    def has_permission(self, request, view):
        """Check the user is authenticated and an admin of at least one organization."""
        return bool(
            request.user
            and request.user.is_authenticated
            and OrganizationMembership.objects.filter(
                user=request.user, role="ADMIN"
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user has admin permissions for this specific organization."""
        return OrganizationMembership.objects.filter(
            organization=obj, user=request.user, role="ADMIN"
        ).exists()


class IsOrganizationMember(BasePermission):
    """Permission class to check if the user is a member of the organization."""

    def has_permission(self, request, view):
        """Check the user is authenticated and a member of at least one organization."""
        return bool(
            request.user
            and request.user.is_authenticated
            and OrganizationMembership.objects.filter(
                user=request.user, is_active=True
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user has member permissions for this specific organization."""
        return OrganizationMembership.objects.filter(
            organization=obj, user=request.user, is_active=True
        ).exists()


class IsOrganizationOrganizer(BasePermission):
    """Permission class to check if the user is an organizer of the organization."""

    def has_permission(self, request, view):
        """Check the user is authenticated and an organizer of at least one organization."""
        return bool(
            request.user
            and request.user.is_authenticated
            and OrganizationMembership.objects.filter(
                user=request.user, role="ORGANIZER"
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user has organizer permissions for this specific organization."""
        return OrganizationMembership.objects.filter(
            organization=obj, user=request.user, role="ORGANIZER"
        ).exists()


class IsOrganizationAdminOrOrganizer(BasePermission):
    """Permission class to check if the user is an admin or organizer of the organization."""

    def has_permission(self, request, view):
        """Check the user is authenticated and an admin or organizer of at least one organization."""
        return bool(
            request.user
            and request.user.is_authenticated
            and OrganizationMembership.objects.filter(
                user=request.user, role__in=["ADMIN", "ORGANIZER"]
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user has admin or organizer permissions for this specific organization."""
        return OrganizationMembership.objects.filter(
            organization=obj,
            user=request.user,
            role__in=["ADMIN", "ORGANIZER"],
        ).exists()


class IsEventOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the event's organization."""

    def has_permission(self, request, view):
        """Check the user is authenticated and an admin of at least one organization."""
        return bool(
            request.user
            and request.user.is_authenticated
            and OrganizationMembership.objects.filter(
                user=request.user, role="ADMIN"
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user is an admin of the organization that owns this event."""
        if not obj.organizer:
            return False
        return OrganizationMembership.objects.filter(
            organization=obj.organizer, user=request.user, role="ADMIN"
        ).exists()


class IsOwner(BasePermission):
    """Permission class to check if the authenticated user owns the object."""

    def has_permission(self, request, view):
        """Require authentication at the view level."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Check if the object's user_account matches the requesting user."""
        return obj.user_account == request.user
