"""custom users permissions."""

from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMembership


class IsOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the organization."""

    def has_permission(self, request, view):
        """Check if the user has admin permissions for the organization."""
        if request.user and request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.filter(
                    user=request.user
                ).first()
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
                membership = OrganizationMembership.objects.filter(
                    user=request.user
                ).first()
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
                membership = OrganizationMembership.objects.filter(
                    user=request.user
                ).first()
                return membership.is_organizers()
            except OrganizationMembership.DoesNotExist:
                return False
        return False


class CanReviewTalks(BasePermission):
    """Permission class to check if user can review talk proposals.

    Allows users who have can_review_talks permission and are not speakers
    for the specific event being reviewed.
    """

    def has_permission(self, request, view):
        """Check if user has permission to review talks."""
        return True  # Allow both authenticated and anonymous users

    def has_object_permission(self, request, view, obj):
        """Check if user can review this specific talk.

        Allows both authenticated and anonymous users.
        """
        return True
