"""custom users' permissions."""

from rest_framework.permissions import BasePermission, IsAuthenticated


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


class IsEmailVerified(IsAuthenticated):
    """Allow only authenticated users whose email address is verified.

    Email/password users become verified by completing the OTP flow. OAuth
    users (Google/GitHub) are verified at signup because the provider has
    already validated their email.
    """

    message = "Email verification is required to perform this action."

    def has_permission(self, request, view):
        """Return True for verified, authenticated users."""
        return super().has_permission(request, view) and request.user.is_email_verified
