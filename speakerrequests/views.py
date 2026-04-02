"""Speaker request views."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer, IsSpeakerRequestRecipient
from speakerrequests.filters import EmailRequestsFilter, SpeakerRequestFilter
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.serializers import (
    EmailRequestsSerializer,
    SpeakerRequestSerializer,
)
from speakerrequests.services import SpeakerRequestService


class OrganizerSpeakerRequestListCreateAPIView(APIView):
    """View for organizers to list and create speaker requests."""

    def get(self, request):
        """Get speaker requests for an organization."""
        queryset = SpeakerRequest.objects.for_organizer(request.user)
        filterset = SpeakerRequestFilter(request.GET, queryset=queryset)
        serializer = SpeakerRequestSerializer(filterset.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new speaker request."""
        # validate request data
        serializer = SpeakerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # create speaker request
        speaker_request = SpeakerRequestService.create_request(
            organizer=serializer.validated_data["organizer"],
            speaker=serializer.validated_data["speaker"],
            event=serializer.validated_data["event"],
            message=serializer.validated_data["message"],
        )
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView(APIView):
    """View for organizers to manage individual speaker requests."""

    serializer_class = SpeakerRequestSerializer
    permission_classes = [IsOrganizationAdminOrOrganizer]

    def get(self, request, speaker_id):
        """Get a single speaker request."""
        queryset = SpeakerRequest.objects.for_organizer(request.user)
        speaker_request = queryset.get(speaker_id=speaker_id)
        serializer = self.serializer_class(speaker_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, speaker_id):
        """Update a single speaker request."""
        queryset = SpeakerRequest.objects.for_organizer(request.user)
        speaker_request = queryset.get(speaker_id=speaker_id)

        # use speaker request service to update status
        req_data = SpeakerRequestService.respond_to_request(
            speaker_request=speaker_request,
            status_update=request.data.get("status"),
        )
        serializer = self.serializer_class(data=req_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerRequestRespondAPIView(APIView):
    """View for speakers to respond to requests (Accept/Reject)."""

    permission_classes = [IsSpeakerRequestRecipient]

    def get(self, request):
        """Get a request for a speaker."""
        speaker_request = SpeakerRequest.objects.for_speaker(request.user)
        serializer = SpeakerRequestSerializer(speaker_request, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update speaker request."""
        speaker_request = SpeakerRequest.objects.get(
            pk=request.data.get("id")
        )  # get request id from request data
        serializer_data = SpeakerRequestService.respond_to_request(
            speaker_request=speaker_request, status_update=request.data.get("status")
        )
        serializer = SpeakerRequestSerializer(serializer_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerEmailRequestListCreateAPIView(APIView):
    """View for email-based speaker requests."""

    serializer_class = EmailRequestsSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EmailRequestsFilter

    def get(self, request):
        """Get email requests for a user."""
        queryset = SpeakerEmailRequests.objects.filter(request_to=request.user)
        filterset = self.filterset_class(request.GET, queryset=queryset)
        serializer = self.serializer_class(filterset.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new email request."""
        speaker_request = SpeakerRequestService.create_email_request(
            request_from=request.user,
            request_to_user=request.data.get("request_to"),
            event=request.data.get("event"),
            message=request.data.get("message"),
        )
        serializer = self.serializer_class(data=speaker_request)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SpeakerEmailRequestRespondAPIView(APIView):
    """View for responding to email-based speaker requests."""

    serializer_class = EmailRequestsSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EmailRequestsFilter

    def patch(self, request, pk=None):
        """Update email request."""
        email_request = SpeakerEmailRequests.objects.get(
            request_to=self.request.user, pk=pk
        )
        response = SpeakerRequestService.respond_to_email_request(
            email_request=email_request, request=request
        )
        serializer = self.serializer_class(data=response)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
