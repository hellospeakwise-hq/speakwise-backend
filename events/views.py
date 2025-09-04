"""Events views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from events.models import Event, Session
from events.serializers import (
    EventSerializer,
    SessionSerializer,
)

from .utils import IsAdminOrOrganizer


@extend_schema(responses={200: EventSerializer})
class EventListAPIView(ListAPIView):
    """View for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    permission_classes = (AllowAny,)
    queryset = Event.objects.all()


@extend_schema(responses={200: EventSerializer})
class EventCreateAPIView(CreateAPIView):
    """View for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    permission_classes = (IsAdminOrOrganizer,)

    def get_queryset(self):
        """Return the user's events."""
        return Event.objects.filter(organizer=self.request.user.organizer_profile_user)


@extend_schema(responses={200: EventSerializer})
class EventRetrieveUpdateDestroyAPIView(APIView):
    """View for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    permission_classes = (IsAuthenticated,)


@extend_schema(request=SessionSerializer, responses={200: SessionSerializer})
class SessionListCreateAPIView(ListCreateAPIView):
    """View for listing and creating sessions."""

    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = (AllowAny,)


@extend_schema(responses={200: SessionSerializer})
class SessionRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting sessions."""

    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = (AllowAny,)


@extend_schema(responses={200: EventSerializer})
class EventDetailAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving event details with extended information."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = (AllowAny,)
