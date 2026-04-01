"""Speaker request views."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from speakerrequests.models import SpeakerRequest, SpeakerEmailRequests
from speakerrequests.serializers import (
    SpeakerRequestSerializer,
    EmailRequestsSerializer,
)
from speakerrequests.services import SpeakerRequestService
from base.permissions import IsSpeakerRequestRecipient, IsOrganizerOfRequest
from speakerrequests.filters import SpeakerRequestFilter, EmailRequestsFilter


class OrganizerSpeakerRequestListCreateAPIView(APIView):
    """View for organizers to list and create speaker requests."""

    serializer_class = SpeakerRequestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get requests for organizations where user is a member."""
        speaker_requests = SpeakerRequest.objects.for_organizer(
            self.request.user
        ).with_prefetch()
        speaker_requests_filter = SpeakerRequestFilter(data=speaker_requests)
        self.serializer_class(speaker_requests_filter.qs)
        return Response(self.serializer_class.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Create a new speaker request using the service layer."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            speaker_request = SpeakerRequestService.create_request(
                organizer=request.user,
                speaker=serializer.validated_data["speaker"],
                event=serializer.validated_data["event"],
                message=serializer.validated_data["message"],
            )
            response_serializer = self.serializer_class(speaker_request)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """View for organizers to manage individual speaker requests."""

    serializer_class = SpeakerRequestSerializer
    permission_classes = [IsAuthenticated, IsOrganizerOfRequest]

    def get_queryset(self):
        """Get requests for organizations where user is a member."""
        return SpeakerRequest.objects.for_organizer(self.request.user).with_prefetches()


class SpeakerIncomingRequestListAPIView(APIView):
    """View for speakers to see incoming requests."""

    serializer_class = SpeakerRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = SpeakerRequestFilter

    def get_queryset(self):
        """Get requests sent to the authenticated speaker."""
        return SpeakerRequest.objects.for_speaker(self.request.user).with_prefetches()


class SpeakerRequestRespondAPIView(generics.UpdateAPIView):
    """View for speakers to respond to requests (Accept/Reject)."""

    serializer_class = SpeakerRequestSerializer
    permission_classes = [IsAuthenticated, IsSpeakerRequestRecipient]

    def get_queryset(self):
        """Get requests sent to the authenticated speaker."""
        return SpeakerRequest.objects.for_speaker(self.request.user)

    def update(self, request, *args, **kwargs):
        """Respond to request using service layer."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        status_update = request.data.get("status")

        try:
            instance = SpeakerRequestService.respond_to_request(
                request_id=instance.pk, user=request.user, status_update=status_update
            )
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SpeakerEmailRequestListCreateAPIView(generics.ListCreateAPIView):
    """View for email-based speaker requests."""

    serializer_class = EmailRequestsSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EmailRequestsFilter

    def get_queryset(self):
        """Get email requests where user is sender or receiver."""
        from django.db.models import Q

        return SpeakerEmailRequests.objects.filter(
            Q(request_from=self.request.user) | Q(request_to=self.request.user)
        )

    def perform_create(self, serializer):
        """Use service layer to create email request."""
        # Note: The original code had some manual reconstruction of request.data
        # We can handle that in the serializer or service.
        SpeakerRequestService.create_email_request(
            request_from=self.request.user,
            request_to_user=serializer.validated_data.get("request_to"),
            event_name=serializer.validated_data["event"],
            location=serializer.validated_data["location"],
            message=serializer.validated_data["message"],
        )


class SpeakerEmailRequestRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """View to manage individual email requests."""

    serializer_class = EmailRequestsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        """Ensure user is the recipient if they are updating status."""
        return SpeakerEmailRequests.objects.filter(request_to=self.request.user)
