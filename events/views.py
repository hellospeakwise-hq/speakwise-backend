"""Events views."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdmin
from events.models import Event
from events.serializers import EventSerializer
from events.utils import create_event_payload


class EventListView(APIView):
    """event list view."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["Events"], responses={200: EventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List events."""
        events = Event.objects.all()
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
            print(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetailView(APIView):
    """get event detail view."""

    def get_permissions(self):
        """Get permissions."""
        if self.request.method in ["GET"]:
            return [AllowAny()]
        return [IsOrganizationAdmin()]

    def get_object(self, pk):
        """Get event object."""
        try:
            return Event.objects.get(pk=pk)
        except Event.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(tags=["Events"], responses={200: EventSerializer})
    def get(self, request, pk, *args, **kwargs):
        """Retrieve event detail."""
        event = self.get_object(pk)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Events"], request=EventSerializer, responses={200: EventSerializer}
    )
    def patch(self, request, pk, *args, **kwargs):
        """Update event detail."""
        event = self.get_object(pk)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            print(serializer.validated_data)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=["Events"], responses={204: None})
    def delete(self, request, pk, *args, **kwargs):
        """Delete event."""
        event = self.get_object(pk)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
