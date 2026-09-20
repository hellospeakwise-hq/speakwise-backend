"""Events views."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsSubmitterOrSuperUser
from events.filters import EventFilter
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
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    @staticmethod
    def _create_serializer(request):
        """Return the serializer used to create an event for this user."""
        if request.user.is_superuser:
            return EventSerializer(data=request.data.copy())
        return EventSubmitSerializer(data=request.data)

    @staticmethod
    def _create_save_kwargs(request):
        """Return extra fields applied when saving a submitted event."""
        extra = {"submitted_by": request.user}
        if not request.user.is_superuser:
            extra["is_active"] = False
        return extra

    @extend_schema(tags=["Events"], responses={200: EventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List published events with broad filtering support."""
        queryset = Event.objects.filter(is_active=True)
        filtered_queryset = EventFilter(request.GET, queryset=queryset).qs
        serializer = EventSerializer(filtered_queryset, many=True)
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


class PublicEventListView(EventListView):
    """Public event catalog view with broad filtering support."""


class PublicEventDetailView(APIView):
    """Public event detail route for active events only."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, slug, *args, **kwargs):
        """Retrieve a public event by slug."""
        event = get_object_or_404(Event, slug=slug, is_active=True)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventDetailView(APIView):
    """Compatibility detail view combining public read + private mutation access."""

    def get_permissions(self):
        """GET is public; mutations require submitter or superuser."""
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated(), IsSubmitterOrSuperUser()]

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, slug, *args, **kwargs):
        """Retrieve a published event, or one the requester may see."""
        if request.user.is_authenticated:
            if request.user.is_superuser:
                event = get_object_or_404(Event, slug=slug)
            else:
                event = get_object_or_404(
                    Event,
                    Q(slug=slug) & (Q(is_active=True) | Q(submitted_by=request.user)),
                )
        else:
            event = get_object_or_404(Event, slug=slug, is_active=True)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSerializer, responses={200: EventSerializer}
    )
    def patch(self, request, slug, *args, **kwargs):
        """Update event detail."""
        event = get_object_or_404(Event, slug=slug)
        self.check_object_permissions(request, event)
        data = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )
        if not request.user.is_superuser:
            data.pop("is_active", None)
        serializer = EventSerializer(event, data=data, partial=True)
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


class PrivateEventDetailView(APIView):
    """Private event management for submitters and admins."""

    permission_classes = [IsAuthenticated, IsSubmitterOrSuperUser]

    def _get_event(self, slug):
        """Return the target event if the requester can manage it."""
        event = get_object_or_404(Event, slug=slug)
        if (
            not self.request.user.is_superuser
            and event.submitted_by != self.request.user
        ):
            raise permissions.PermissionDenied("You do not have access to this event.")
        return event

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, slug, *args, **kwargs):
        """Retrieve a pending or active event that the user manages."""
        event = self._get_event(slug)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSerializer, responses={200: EventSerializer}
    )
    def patch(self, request, slug, *args, **kwargs):
        """Update a managed event, while preventing self-approval."""
        event = self._get_event(slug)
        data = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )
        if not request.user.is_superuser:
            data.pop("is_active", None)
        serializer = EventSerializer(event, data=data, partial=True)
        if serializer.is_valid():
            event = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Events"], responses={204: None})
    def delete(self, request, slug, *args, **kwargs):
        """Delete a managed event."""
        event = self._get_event(slug)
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


class PrivateEventListView(APIView):
    """Return the current user's submitted events."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all events submitted by the authenticated user."""
        events = Event.objects.filter(submitted_by=request.user)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyEventsListView(PrivateEventListView):
    """Backward-compatible alias for the current-user events route."""

    pass
