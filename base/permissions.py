"""custom permissions."""

from rest_framework.permissions import BasePermission


class IsAdminOrOrganizer(BasePermission):
    """custom admin or organizer permission class."""

    def has_permission(self, request, view):
        """Has permission."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_organizer_or_admin", lambda: False)()


class IsAdminOrSpeaker(BasePermission):
    """custom admin or speaker permission class."""

    def has_permission(self, request, view):
        """Has permission."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_speaker_or_admin", lambda: False)()


class IsAdminOrAttendee(BasePermission):
    """custom admin or attendee permission class."""

    def has_permission(self, request, view):
        """Has permission."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_attendee_or_admin", lambda: False)()


class IsSpeakerOrAttendee(BasePermission):
    """custom speaker or attendee permission class."""

    def has_permission(self, request, view):
        """Has permission."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_speaker_or_attendee", lambda: False)()


class IsAdminOrOrganizerOrSpeaker(BasePermission):
    """custom admin or organizer or speaker permission class."""

    def has_permission(self, request, view):
        """Has permission."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_admin_or_organizer_or_speaker", lambda: False)()
