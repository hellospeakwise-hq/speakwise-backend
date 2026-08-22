"""Events views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsSuperUser
from events.models import Event, Tag
from events.serializers import (
    CFPMarketSerializer,
    EventSerializer,
    EventSubmitSerializer,
    TagSerializer,
)
from events.utils import create_event_payload


class TagListView(APIView):
    """List and create event tags."""

    def get_permissions(self):
        """GET is public; POST requires superuser."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsSuperUser()]

    @extend_schema(tags=["Tags"], responses={200: TagSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List all tags."""
        tags = Tag.objects.all().order_by("name")
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(tags=["Tags"], request=TagSerializer, responses={201: TagSerializer})
    def post(self, request, *args, **kwargs):
        """Create a new tag."""
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventListView(APIView):
    """List published events and accept new event submissions."""

    def get_permissions(self):
        """GET is public; POST requires an authenticated user."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def _create_serializer(self, request):
        """Return the serializer used to create an event for this user."""
        if request.user.is_superuser:
            return EventSerializer(data=create_event_payload(request))
        return EventSubmitSerializer(data=request.data)

    def _create_save_kwargs(self, request):
        """Return extra fields applied when saving a submitted event."""
        extra = {"submitted_by": request.user}
        if not request.user.is_superuser:
            extra["is_active"] = False
        return extra

    @extend_schema(tags=["Events"], responses={200: EventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List published events."""
        events = Event.objects.published().with_listing_relations()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSubmitSerializer, responses={201: EventSerializer}
    )
    def post(self, request, *args, **kwargs):
        """Submit an event. Regular users create a listing pending approval."""
        serializer = self._create_serializer(request)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        event = serializer.save(**self._create_save_kwargs(request))
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class CFPMarketListView(APIView):
    """Public list of events with a currently open CFP."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["CFP Market"], responses={200: CFPMarketSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Return events whose CFP is currently open for the CFP Market."""
        events = Event.objects.with_open_cfp().prefetch_related("tags")
        serializer = CFPMarketSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventDetailView(APIView):
    """get event detail view."""

    def get_permissions(self):
        """Get permissions."""
        if self.request.method in ["GET"]:
            return [AllowAny()]
        return [IsSuperUser()]

    def _get_visible_event(self, request, slug):
        """Return the event if the requester is allowed to view it."""
        return get_object_or_404(
            Event.objects.visible_to(request.user).with_listing_relations(),
            slug=slug,
        )

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, slug, *args, **kwargs):
        """Retrieve a published event, or an unpublished one the user may see."""
        event = self._get_visible_event(request, slug)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSerializer, responses={200: EventSerializer}
    )
    def patch(self, request, slug, *args, **kwargs):
        """Update event detail."""
        event = self._get_visible_event(request, slug)
        self.check_object_permissions(request, event)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Events"], responses={204: None})
    def delete(self, request, slug, *args, **kwargs):
        """Delete event."""
        event = self._get_visible_event(request, slug)
        self.check_object_permissions(request, event)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventReviewListView(APIView):
    """List events that are waiting for approval before publication."""

    permission_classes = [IsSuperUser]

    @extend_schema(tags=["Events"], responses={200: EventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Return unpublished event submissions for review."""
        events = Event.objects.pending_review().with_listing_relations()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventApproveView(APIView):
    """Approve a submitted event so it becomes publicly visible."""

    permission_classes = [IsSuperUser]

    @extend_schema(tags=["Events"], request=None, responses={200: EventSerializer})
    def post(self, request, slug, *args, **kwargs):
        """Mark the event as published."""
        event = get_object_or_404(Event, slug=slug)
        self.check_object_permissions(request, event)
        if not event.is_active:
            event.is_active = True
            event.save(update_fields=["is_active", "updated_at"])
        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)


class EventSpeakerDeckToggleView(APIView):
    """Toggle speaker deck upload for an event.

    POST toggles the speaker_deck_upload_enabled flag.
    When enabling, sends notifications to all accepted speakers.
    """

    permission_classes = [IsSuperUser]

    @extend_schema(
        tags=["Events"],
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "speaker_deck_upload_enabled": {"type": "boolean"},
                    "detail": {"type": "string"},
                },
            }
        },
    )
    def post(self, request, slug, *args, **kwargs):
        """Toggle the speaker deck upload flag for an event."""
        from events.notifications import notify_accepted_speakers_deck_upload

        event = get_object_or_404(Event, slug=slug)
        self.check_object_permissions(request, event)

        # Toggle the flag
        event.speaker_deck_upload_enabled = not event.speaker_deck_upload_enabled
        event.save(update_fields=["speaker_deck_upload_enabled", "updated_at"])

        detail = "Speaker deck upload has been "
        if event.speaker_deck_upload_enabled:
            detail += "enabled."
            notify_accepted_speakers_deck_upload(event)
        else:
            detail += "disabled."

        return Response(
            {
                "speaker_deck_upload_enabled": event.speaker_deck_upload_enabled,
                "detail": detail,
            },
            status=status.HTTP_200_OK,
        )
