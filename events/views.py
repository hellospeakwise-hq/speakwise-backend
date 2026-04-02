"""Events views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer
from events.models import Event, Tag
from events.serializers import EventSerializer, TagSerializer
from events.models import Event, EventSpeakers
from events.serializers import EventSerializer
from events.utils import create_event_payload
from organizations.models import OrganizationMembership


class TagListView(APIView):
    """List and create event tags."""

    def get_permissions(self):
        """GET is public; POST requires organizer/admin."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsOrganizationAdminOrOrganizer()]

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
    """event list view."""

    def get_permissions(self):
        """Get permissions."""
        if self.request.method in ["GET"]:
            return [AllowAny()]
        return [IsOrganizationAdminOrOrganizer()]

    @extend_schema(tags=["Events"], responses={200: EventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List events."""
        events = Event.objects.all()
        if request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.get(user=request.user)
                events = events.filter(organizer=membership.organization)
            except OrganizationMembership.DoesNotExist:
                events = events.filter(is_active=True)
        else:
            events = events.filter(is_active=True)

        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSerializer, responses={201: EventSerializer}
    )
    def post(self, request, *args, **kwargs):
        """Create event."""
        payload = create_event_payload(request)
        serializer = EventSerializer(data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetailView(APIView):
    """get event detail view."""

    def get_permissions(self):
        """Get permissions."""
        if self.request.method in ["GET"]:
            return [AllowAny()]
        return [IsOrganizationAdminOrOrganizer()]

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, slug, *args, **kwargs):
        """Retrieve event detail."""
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Events"], responses={204: None})
    def delete(self, request, slug, *args, **kwargs):
        """Delete event."""
        event = get_object_or_404(Event, slug=slug)
        self.check_object_permissions(request, event)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventSpeakersListView(APIView):
    """get event speakers list view."""

    def get(self, request, event_slug: str):
        """Retrieve event speakers."""
        speakers = EventSpeakers.objects.filter(event__slug=event_slug)
        serializer = EventSerializer(speakers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
