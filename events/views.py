"""Events views."""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from events.filters import EventFilter
from events.models import Event
from events.permissions import EventPermission
from events.serializers import EventSerializer


@extend_schema(responses={200: EventSerializer})
class EventListCreateAPIView(ListCreateAPIView):
    """View for listing and creating events."""

    serializer_class = EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EventFilter

    def get_queryset(self):
        """Return events based on request method and user permissions."""
        queryset = Event.objects.all()
        # For authenticated users making GET requests, show all events
        if self.request.method == "GET":
            return queryset.order_by("-created_at")

        # For POST requests, this is just for permission checking
        return queryset

    def get_permissions(self):
        """Get permissions based on request method."""
        if self.request.method == "POST":
            permission_classes = (IsAuthenticated, EventPermission)
        else:
            permission_classes = (AllowAny,)
        return [permission() for permission in permission_classes]


@extend_schema(responses={200: EventSerializer})
class EventDetailAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting event details."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_permissions(self):
        """Get permissions based on request method."""
        if self.request.method == "GET":
            permission_classes = (AllowAny,)
        else:
            permission_classes = (IsAuthenticated, EventPermission)
        return [permission() for permission in permission_classes]


# Legacy view for backward compatibility
@extend_schema(responses={200: EventSerializer})
class EventRetrieveUpdateDestroyAPIView(APIView):
    """Legacy view for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    permission_classes = (IsAuthenticated,)
