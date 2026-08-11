"""Feedback views using Generic Views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest

from .models import EventFeedbackPreference, Feedback
from .serializers import EventFeedbackPreferenceSerializer, FeedbackSerializer


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

        Rejected when the speaker has closed feedback for the given event.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        speaker = serializer.validated_data.get("speaker")
        event = serializer.validated_data["event"]
        if speaker and not EventFeedbackPreference.objects.is_enabled_for(
            speaker, event
        ):
            raise PermissionDenied(
                "This speaker is not accepting feedback for this event."
            )

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Feedbacks"])
class EventFeedbackPreferenceView(APIView):
    """Read or set the authenticated speaker's feedback preference for an event.

    GET returns the current preference (open by default when none has been set).
    PUT sets it explicitly with {"is_feedback_enabled": true|false}.
    Only speakers with an accepted speaker request for the event may access it.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EventFeedbackPreferenceSerializer

    def get_speaker(self, user, event):
        """Return the user's profile when accepted to speak at the event."""
        speaker = user.speakers_profile_user.first()
        if speaker is None:
            raise PermissionDenied("Speaker profile not found for this user.")

        is_accepted = SpeakerRequest.objects.filter(
            speaker=speaker,
            event=event,
            status=RequestStatusChoices.ACCEPTED,
        ).exists()
        if not is_accepted:
            raise PermissionDenied("You are not an accepted speaker for this event.")
        return speaker

    @extend_schema(responses=EventFeedbackPreferenceSerializer)
    def get(self, request, event_id, *args, **kwargs):
        """Return the speaker's feedback preference for the event."""
        event = get_object_or_404(Event, pk=event_id)
        speaker = self.get_speaker(request.user, event)

        preference = event.speaker_feedback_preferences.filter(
            speaker=speaker
        ).first() or EventFeedbackPreference(
            speaker=speaker, event=event, is_feedback_enabled=True
        )
        serializer = self.serializer_class(preference)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=EventFeedbackPreferenceSerializer,
        responses=EventFeedbackPreferenceSerializer,
    )
    def put(self, request, event_id, *args, **kwargs):
        """Set the speaker's feedback preference for the event."""
        event = get_object_or_404(Event, pk=event_id)
        speaker = self.get_speaker(request.user, event)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        preference = EventFeedbackPreference.objects.set_for(
            speaker,
            event,
            serializer.validated_data["is_feedback_enabled"],
        )
        return Response(
            self.serializer_class(preference).data, status=status.HTTP_200_OK
        )
