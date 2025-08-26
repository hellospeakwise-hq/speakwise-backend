"""Events views."""

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from organizers.models import OrganizerProfile
from events.models import Country, Event, Session, Tag
from events.serializers import (
    CountrySerializer,
    EventSerializer,
    SessionSerializer,
    TagSerializer,
)


def is_organizer_or_admin(user):
    """Helper method to check if user is organizer or admin."""
    return (
        hasattr(user, "role")
        and user.role
        and user.role.display in ["organizer", "admin"]
    )


def is_organizer(user):
    """Helper method to check if user is organizer."""
    return hasattr(user, "role") and user.role and user.role.display == "organizer"


@extend_schema(request=EventSerializer, responses={200: EventSerializer})
class EventListCreateAPIView(ListCreateAPIView):
    """View for listing and creating events."""

    serializer_class = EventSerializer
    permission_classes = (IsAuthenticated)

    def get_queryset(self):
        """
        Return all events for any authenticated user.
        For organizers, only show their own events for editing.
        """
        user = self.request.user
        if user.is_authenticated:
            # Check if user is an organizer - if so, show only their events
            if is_organizer(user):
                try:
                    organizer = OrganizerProfile.objects.get(user_id=user)
                    return Event.objects.filter(organizer=organizer)
                except OrganizerProfile.DoesNotExist:
                    return Event.objects.none()
            # For all other authenticated users, show all events
            return Event.objects.all()
        return Event.objects.none()

    def perform_create(self, serializer):
        """Set the organizer when creating an event."""
        user = self.request.user

        # Only organizers and admins can create events
        if is_organizer_or_admin(user):
            try:
                organizer = OrganizerProfile.objects.get(user_id=user)
                serializer.save(organizer=organizer)
            except OrganizerProfile.DoesNotExist:
                # Create organizer profile if it doesn't exist
                organizer = OrganizerProfile.objects.create(
                    user_id=user,
                    organization=(
                        f"{user.first_name or ''} {user.last_name or ''}".strip()
                        or getattr(user, "username", None)
                        or getattr(user, "email", "Organizer")
                    ),
                )
                serializer.save(organizer=organizer)
        else:
            # Return permission denied for non-organizers
            raise PermissionDenied(
                detail="Only organizers and admins can create events."
            )


@extend_schema(responses={200: EventSerializer})
class EventRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting events."""

    serializer_class = EventSerializer
    permission_classes = (IsAuthenticated)

    def get_queryset(self):
        """
        Return all events for any authenticated user.
        For organizers, only show their own events for editing.
        """
        user = self.request.user
        if user.is_authenticated:
            # For read operations, show all events
            if self.request.method == "GET":
                return Event.objects.all()

            # For write operations, only allow OrganizerProfile to modify their own
            # events
            if is_organizer_or_admin(user):
                try:
                    organizer = OrganizerProfile.objects.get(user_id=user)
                    return Event.objects.filter(organizer=organizer)
                except OrganizerProfile.DoesNotExist:
                    return Event.objects.none()
            return Event.objects.none()
        return Event.objects.none()


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


@extend_schema(request=CountrySerializer, responses={200: CountrySerializer})
class CountryListCreateAPIView(ListCreateAPIView):
    """View for listing and creating countries."""

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (AllowAny,)


@extend_schema(responses={200: CountrySerializer})
class CountryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting countries."""

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (AllowAny,)


@extend_schema(request=TagSerializer, responses={200: TagSerializer})
class TagListCreateAPIView(ListCreateAPIView):
    """View for listing and creating tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


@extend_schema(responses={200: TagSerializer})
class TagRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


@extend_schema(responses={200: EventSerializer})
class EventDetailAPIView(RetrieveUpdateDestroyAPIView):
    """View for retrieving event details with extended information."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = (AllowAny,)
