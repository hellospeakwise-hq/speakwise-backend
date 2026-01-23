"""Events views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from base.permissions import IsOrganizationAdmin
from events.models import Event
from events.serializers import EventSerializer
from events.utils import create_event_payload


class EventListView(ListCreateAPIView):
    """Event list and create view."""

    queryset = (
        Event.objects.all()
        .select_related("location", "organizer")
        .prefetch_related("tags")
    )
    serializer_class = EventSerializer

    def get_permissions(self):
        """Get permissions."""
        if self.request.method == "POST":
            return [IsOrganizationAdmin()]
        return [AllowAny()]

    @extend_schema(tags=["Events"])
    def post(self, request, *args, **kwargs):
        """Create event."""
        payload = create_event_payload(request)
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class EventDetailView(RetrieveUpdateDestroyAPIView):
    """Event retrieve, update and delete view."""

    queryset = (
        Event.objects.all()
        .select_related("location", "organizer")
        .prefetch_related("tags")
    )
    serializer_class = EventSerializer

    def get_permissions(self):
        """Get permissions."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsOrganizationAdmin()]
