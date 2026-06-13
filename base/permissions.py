"""custom users permissions."""

from typing import Protocol

from rest_framework.permissions import BasePermission

from organizations.models import Organization, OrganizationMembership


class OrganizationScoped(Protocol):
    """Protocol for models that have an organization they belong to."""

    @property
    def organization(self):
        """The organization this model belongs to."""
        ...


def resolve_organization(obj):
    """Walk up the ownership chain to find the organization.

    Handles:
    - Organization itself
    - Models with an ``organizer`` FK to Organization (e.g. Event)
    - Models with an ``event`` FK whose event has an organizer (e.g. Session)
    - Models with an ``organization`` FK directly (e.g. SpeakerRequest)
    """
    if isinstance(obj, Organization):
        return obj
    if hasattr(obj, "organizer"):
        org = obj.organizer
        if isinstance(org, Organization):
            return org
    if hasattr(obj, "organization"):
        org = obj.organization
        if isinstance(org, Organization):
            return org
    if hasattr(obj, "event"):
        event = obj.event
        if hasattr(event, "organizer"):
            org = event.organizer
            if isinstance(org, Organization):
                return org
    return None


class IsOrganizationAdmin(BasePermission):
    """Permission class to check if the user is an admin of the organization."""

    def has_permission(self, request, view):
        """Check if the user is authenticated before checking object permissions."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if the user has admin permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = resolve_organization(obj)
            if organization is None:
                return False
            return OrganizationMembership.objects.filter(
                organization=organization, user=request.user, role="ADMIN"
            ).exists()
        return False


class IsOrganizationMember(BasePermission):
    """Permission class to check if the user is a member of the organization."""

    def has_permission(self, request, view):
        """Check if the user is authenticated before checking object permissions."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if the user has member permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = resolve_organization(obj)
            if organization is None:
                return False
            return OrganizationMembership.objects.filter(
                organization=organization, user=request.user, is_active=True
            ).exists()
        return False


class IsOrganizationOrganizer(BasePermission):
    """Permission class to check if the user is an organizer of the organization."""

    def has_permission(self, request, view):
        """Check if the user is authenticated before checking object permissions."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if the user has organizer permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = resolve_organization(obj)
            if organization is None:
                return False
            return OrganizationMembership.objects.filter(
                organization=organization, user=request.user, role="ORGANIZER"
            ).exists()
        return False


class IsOrganizationAdminOrOrganizer(BasePermission):
    """Permission class to check if the user is an admin or organizer of the organization."""

    def has_permission(self, request, view):
        """Check if the user is authenticated before checking object permissions."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if the user has admin or organizer permissions for the organization."""
        if request.user and request.user.is_authenticated:
            organization = resolve_organization(obj)
            if organization is None:
                return False
            return OrganizationMembership.objects.filter(
                organization=organization,
                user=request.user,
                role__in=["ADMIN", "ORGANIZER"],
            ).exists()
        return False
