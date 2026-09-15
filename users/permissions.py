"""Custom DRF permission classes for the users app."""

from rest_framework.permissions import IsAuthenticated


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
