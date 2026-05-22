"""event schedule views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer
from events.models import Event

from .models import EventSchedule
from .serializers import EventScheduleSerializer


@extend_schema(
    tags=["Event Schedules"],
    request=EventScheduleSerializer,
    responses=EventScheduleSerializer,
)
class EventScheduleListCreateView(APIView):
    """Event schedule list create view."""

    permission_classes = [IsOrganizationAdminOrOrganizer]

    def get(self, request, event_slug):
        """List event schedules.

        Query params: event_slug.
        Response: EventSchedule object.
        """
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        event = get_object_or_404(Event, slug=event_slug)
        self.check_object_permissions(request, event)
        event_schedules = EventSchedule.objects.filter(event=event)
        serializer = EventScheduleSerializer(event_schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, event_slug):
        """Create an event schedule."""
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        event = get_object_or_404(Event, slug=event_slug)
        self.check_object_permissions(request, event)
        serializer = EventScheduleSerializer(
            data=request.data, context={"request": request, "event": event}
        )
        if serializer.is_valid():
            serializer.save()
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
        serializer = EventScheduleSerializer(
            event_schedule,
            data=request.data,
            context={"event": event_schedule.event},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, schedule_id):
        """Update event schedule."""
        event_schedule = get_object_or_404(EventSchedule, id=schedule_id)
        self.check_object_permissions(request, event_schedule)
        serializer = EventScheduleSerializer(
            event_schedule,
            data=request.data,
            context={"event": event_schedule.event},
            partial=True,
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
