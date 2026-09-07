"""custom users' permissions."""

from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """Permission class to check if the user is a superuser."""

    def has_permission(self, request, view):
        """Check if the user is authenticated and is a superuser."""
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user is a superuser."""
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class IsSubmitterOrSuperUser(BasePermission):
    """Allow safe methods for anyone; mutations for submitter or superuser."""

    def has_permission(self, request, view):
        """Check if the user is authenticated."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Allow submitter or superuser to perform operations on the object."""
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return getattr(obj, "submitted_by", None) == request.user
