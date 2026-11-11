"""Custom permissions for the profiles app."""

from base.permissions import IsEmailVerified


class IsOrganizationOwnerOrSuperUser(IsEmailVerified):
    """Allow changes to an organization only by its verified owner or a superuser.

    Inherits the email-verification check, so views need only this one class.
    The ownership check is object-level: views must call
    ``check_object_permissions`` after loading the organization. Ownerless
    organizations (``owner`` is null) can only be changed by superusers.
    """

    owner_message = "You do not have permission to modify this organization."

    def has_object_permission(self, request, view, obj):
        """Return True when the requester owns the organization or is a superuser."""
        user = request.user
        if user.is_superuser or (obj.owner_id is not None and obj.owner_id == user.id):
            return True
        # DRF reports the failing permission's ``message``. Swap it here so an
        # unverified user still sees the email message from ``has_permission``.
        self.message = self.owner_message
        return False
