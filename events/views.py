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
from events.serializers import EventSerializer


@extend_schema(responses={200: EventSerializer})
class EventListCreateAPIView(ListCreateAPIView):
    """View for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EventFilter

    def get_queryset(self):
        """Return the user's events."""
        if self.request.method == "POST":
            return Event.objects.all()
        if self.request.method == "GET":
            return Event.objects.all()

    def get_permissions(self):
        """Get permissions."""
        if self.request.method == "POST":
            permission_classes = (IsAuthenticated,)
        else:
            permission_classes = (AllowAny,)
        return [permission() for permission in permission_classes]


@extend_schema(responses={200: EventSerializer})
class EventRetrieveUpdateDestroyAPIView(APIView):
    """View for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    permission_classes = (IsAuthenticated,)


@extend_schema(responses={200: EventSerializer})
class EventDetailAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving event details with extended information."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = (AllowAny,)
