"""Events views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsSuperUser
from events.models import Event
from events.serializers import (
    CFPMarketSerializer,
    EventSerializer,
    EventSubmitSerializer,
)


class EventListView(APIView):
    """Public event listing and community event submission."""

    def get_permissions(self):
        """GET is public; POST requires an authenticated user."""
        if self.request.method == permissions.SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def _create_serializer(self, request):
        """Return the serializer used to create an event for this user."""
        if request.user.is_superuser:
            return EventSerializer(data=request.data.copy())
        return EventSubmitSerializer(data=request.data)

    def _create_save_kwargs(self, request):
        """Return extra fields applied when saving a submitted event."""
        extra = {"submitted_by": request.user}
        if not request.user.is_superuser:
            extra["is_active"] = False
        return extra

    @extend_schema(tags=["Events"], responses={200: EventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List published events for the general event listing."""
        events = Event.objects.filter(is_active=True).select_related("submitted_by")
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"],
        request=EventSubmitSerializer,
        responses={201: EventSerializer},
    )
    def post(self, request, *args, **kwargs):
        """Submit an event. Regular users create a listing pending approval."""
        serializer = self._create_serializer(request)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        event = serializer.save(**self._create_save_kwargs(request))
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    """get event detail view."""

    def get_permissions(self):
        """GET is public; mutations require superuser."""
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        return [IsSuperUser()]

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, slug, *args, **kwargs):
        """Retrieve a published event, or one the requester may see."""
        event = get_object_or_404(Event, slug=slug)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSerializer, responses={200: EventSerializer}
    )
    def patch(self, request, slug, *args, **kwargs):
        """Update event detail."""
        event = get_object_or_404(Event, slug=slug)
        self.check_object_permissions(request, event)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            event = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Events"], responses={204: None})
    def delete(self, request, slug, *args, **kwargs):
        """Delete event."""
        event = get_object_or_404(Event, slug=slug)
        self.check_object_permissions(request, event)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CFPMarketListView(APIView):
    """Public list of events with a currently open CFP."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["CFP Market"], responses={200: CFPMarketSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Return events whose CFP is currently open for the CFP Market."""
        events = Event.objects.with_open_cfp()
        serializer = CFPMarketSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyEventsListView(APIView):
    """Return events created by a user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get method."""
        events = Event.objects.filter(submitted_by=request.user)
        serializer = EventSerializer(data=events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
