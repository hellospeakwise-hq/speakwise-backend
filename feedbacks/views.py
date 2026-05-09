"""Feedback views using Generic Views."""

from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendees.models import Attendance
from events.models import Event
from speakerrequests.models import SpeakerRequest
from speakers.models import SpeakerProfile

from .models import Feedback, SpeakerFeedbackSettings
from .serializers import FeedbackSerializer


class FeedbackListCreateView(APIView):
    """List and create feedback."""

    serializer_class = FeedbackSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(responses=FeedbackSerializer(many=True))
    def get(self, request, *args, **kwargs):
        """List feedbacks for the authenticated speaker."""
        feedbacks = Feedback.objects.filter(speaker__user_account=request.user)
        serializer = self.serializer_class(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=FeedbackSerializer, responses=FeedbackSerializer)
    def post(self, request, *args, **kwargs):
        """Create a new feedback.

        Requires prior attendee verification via the verify endpoint.
        If not verified, returns 403 with a link to the verification endpoint.
        Blocked when the speaker has disabled feedback for the given event.
        """
        if not request.session.get("attendee_verified"):
            verify_url = reverse("attendees:verify-attendee")
            # Namespace is mounted under /api/ at project level
            return Response(
                {
                    "detail": "Attendee verification required before submitting feedback.",
                    "verify_url": f"/api/{verify_url.lstrip('/')}",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check whether the speaker has disabled feedback for this event.
        speaker = serializer.validated_data.get("speaker")
        event = serializer.validated_data.get("event")
        if speaker and event:
            try:
                fb_settings = SpeakerFeedbackSettings.objects.get(
                    speaker=speaker, event=event
                )
                if not fb_settings.feedback_enabled:
                    return Response(
                        {"detail": "The speaker has disabled feedback for this event."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except SpeakerFeedbackSettings.DoesNotExist:
                pass  # No explicit setting means feedback is enabled by default.

        serializer.save()

        # Mark attendance as having given feedback based on verified email.
        email = request.session.get("attendee_email")
        if email:
            Attendance.objects.filter(email=email, is_given_feedback=False).update(
                is_given_feedback=True
            )

        # Clear verification flags after successful submission.
        request.session["attendee_verified"] = False
        request.session.pop("attendee_email", None)
        request.session.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SpeakerFeedbackToggleView(APIView):
    """Toggle feedback collection for a speaker's talk at a specific event.

    POST toggles the feedback_enabled flag for the authenticated speaker at the
    given event. The speaker must have an accepted speaker request for that event.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Feedbacks"],
        request={
            "type": "object",
            "properties": {"event": {"type": "string", "format": "uuid"}},
            "required": ["event"],
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "feedback_enabled": {"type": "boolean"},
                    "detail": {"type": "string"},
                },
            }
        },
    )
    def post(self, request, *args, **kwargs):
        """Toggle feedback enabled/disabled for the speaker at the given event."""
        try:
            speaker = SpeakerProfile.objects.get(user_account=request.user)
        except SpeakerProfile.DoesNotExist:
            return Response(
                {"detail": "Speaker profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        event_id = request.data.get("event")
        if not event_id:
            return Response(
                {"detail": "event is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event = get_object_or_404(Event, id=event_id)

        # Only accepted speakers may control feedback settings for an event.
        if not SpeakerRequest.objects.filter(
            speaker=speaker, event=event, status="accepted"
        ).exists():
            return Response(
                {"detail": "You are not an accepted speaker for this event."},
                status=status.HTTP_403_FORBIDDEN,
            )

        settings, _ = SpeakerFeedbackSettings.objects.get_or_create(
            speaker=speaker,
            event=event,
            defaults={"feedback_enabled": True},
        )
        settings.feedback_enabled = not settings.feedback_enabled
        settings.save(update_fields=["feedback_enabled", "updated_at"])

        detail = "Feedback has been " + (
            "enabled." if settings.feedback_enabled else "disabled."
        )
        return Response(
            {"feedback_enabled": settings.feedback_enabled, "detail": detail},
            status=status.HTTP_200_OK,
        )
