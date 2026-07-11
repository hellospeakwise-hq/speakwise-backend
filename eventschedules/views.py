"""event schedule views."""

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer
from events.models import Event
from eventschedules.utils import create_event_schedule_payload

from .models import EventSchedule
from .serializers import EventScheduleSerializer


@extend_schema(
    tags=["Event Schedules"],
    request=EventScheduleSerializer,
    responses=EventScheduleSerializer,
)
class EventScheduleListCreateView(APIView):
    """Event schedule list create view."""

    def get_permissions(self):
        """Get permission class."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsOrganizationAdminOrOrganizer()]

    def get(self, request, event_slug):
        """List event schedules.

        Query params: event_slug.
        Response: EventSchedule object.
        """
        event = get_object_or_404(Event, slug=event_slug)
        event_schedule = EventSchedule.objects.filter(event=event).first()
        serializer = EventScheduleSerializer(event_schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, event_slug):
        """Create an event schedule."""
        event = get_object_or_404(Event, slug=event_slug)
        self.check_object_permissions(request, event.id)
        try:
            payload = create_event_schedule_payload(event)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EventScheduleSerializer(data=payload)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response(
                    {"detail": "Event schedule already exists for this event."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Event Schedules"],
    request=EventScheduleSerializer,
    responses=EventScheduleSerializer,
)
class EventScheduleRetrieveUpdateDestroyView(APIView):
    """Event schedule retrieve update destroy view."""

    permission_classes = [IsOrganizationAdminOrOrganizer]

    def get(self, request, schedule_id):
        """Retrieve event schedule."""
        event_schedule = get_object_or_404(EventSchedule, id=schedule_id)
        self.check_object_permissions(request, event_schedule)
        serializer = EventScheduleSerializer(event_schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, schedule_id):
        """Update event schedule."""
        event_schedule = get_object_or_404(EventSchedule, id=schedule_id)
        self.check_object_permissions(request, event_schedule)
        serializer = EventScheduleSerializer(event_schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, schedule_id):
        """Update event schedule."""
        event_schedule = get_object_or_404(EventSchedule, id=schedule_id)
        self.check_object_permissions(request, event_schedule)
        serializer = EventScheduleSerializer(
            event_schedule, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, schedule_id):
        """Delete event schedule."""
        event_schedule = get_object_or_404(EventSchedule, id=schedule_id)
        self.check_object_permissions(request, event_schedule)
        event_schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
