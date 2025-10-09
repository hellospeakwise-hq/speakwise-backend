"""talks permissions."""

from rest_framework.permissions import BasePermission

from talks.models import Talks


class CanReviewTalks(BasePermission):
    """Permission class to check if user can review talks."""

    def has_permission(self, request, view):
        """Check if user has permission to access review endpoint."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # Allow talk reviewers, organizers, and admins
        return (
            user.is_talk_reviewer()
            or user.is_organizer()
            or user.is_admin()
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can review this specific talk."""
        user = request.user

        # Get the talk's event
        talk = obj if isinstance(obj, Talks) else None
        if not talk:
            return False

        # Check if user is a speaker for this event
        # If user has a speaker profile and has talks in this event, deny access
        try:
            speaker_profile = user.speakers_profile_user.first()
            if speaker_profile:
                # Check if this speaker has any talks in the same event
                has_talks_in_event = Talks.objects.filter(
                    speaker=speaker_profile,
                    event=talk.event
                ).exists()

                if has_talks_in_event:
                    return False
        except Exception:
            # If no speaker profile exists, allow access
            pass

        return True
