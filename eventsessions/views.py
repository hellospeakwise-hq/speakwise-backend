"""API views for managing event sessions.

This module provides endpoints for listing, creating, retrieving,
updating, and deleting sessions associated with specific events.
"""

from uuid import UUID

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer
from events.models import Event
from eventsessions.models import Session
from eventsessions.serializers import SessionSerializer


@extend_schema(
    responses=SessionSerializer, request=SessionSerializer, tags=["Event Sessions"]
)
class SessionListCreateView(APIView):
    """View for listing all sessions of an event and creating new sessions."""

    serializer_class = SessionSerializer
    permission_classes = [IsOrganizationAdminOrOrganizer]

    def get(self, request):
        """List all sessions associated with a specific event.

        Returns a list of all sessions associated with a specific event (identified by slug).
        Accessible by any user.
        """
        event_slug = request.query_params.get("event")
        if not event_slug:
            return Response(
                data="event slug required in query params",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = get_object_or_404(Event, slug=event_slug)
            sessions = Session.objects.filter(event=event)
        except Event.DoesNotExist as err:
            return Response(err, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new session for the specified event.

        Only accessible by organization admins or organizers.
        """
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    responses=SessionSerializer, request=SessionSerializer, tags=["Event Sessions"]
)
class SessionDetailView(APIView):
    """View for retrieving, updating, and deleting a specific session."""

    permission_classes = [IsOrganizationAdminOrOrganizer]
    serializer_class = SessionSerializer

    def get(self, request, session_id: UUID):
        """Retrieve the details of a specific session.

        Returns the details of a session identified by its UUID.
        Requires organization admin or organizer permissions.
        """
        session = get_object_or_404(Session, id=session_id)
        self.check_object_permissions(request, session)
        serializer = self.serializer_class(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, session_id: UUID):
        """Partially update an existing session.

        Requires organization admin or organizer permissions.
        """
        session = get_object_or_404(Session, id=session_id)
        self.check_object_permissions(request, session)
        serializer = self.serializer_class(session, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, session_id: UUID):
        """Fully update an existing session.

        Requires organization admin or organizer permissions.
        """
        session = get_object_or_404(Session, id=session_id)
        self.check_object_permissions(request, session)
        serializer = self.serializer_class(session, data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, session_id: UUID):
        """Remove the specified session.

        Requires organization admin or organizer permissions.
        """
        session = get_object_or_404(Session, id=session_id)
        self.check_object_permissions(request, session)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses=SessionSerializer, tags=["Event Sessions"])
class SessionPublicListView(APIView):
    """View for listing all sessions of an event for public use."""

    permission_classes = [AllowAny]
    serializer_class = SessionSerializer

    def get(self, request, event_slug: str):
        """List all published sessions of an event.

        Returns a list of all sessions associated with a specific event (identified by slug)
        that are not in draft status. Accessible by any user.
        """
        try:
            sessions = Session.objects.filter(event__slug=event_slug, is_draft=False)
            serializer = self.serializer_class(sessions, many=True)
        except Event.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)
