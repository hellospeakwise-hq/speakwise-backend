"""speaker request views."""

from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.serializers import (
    EmailSpeakerRequestsSerializer,
    OrganizationSpeakerRequestCancelSerializer,
    SpeakerRequestAcceptDeclineSerializer,
    SpeakerRequestSerializer,
    SpeakerRequestUpdateSerializer,
)
from speakerrequests.services import (
    notify_speaker_email_request,
    notify_speaker_of_org_request,
    notify_speaker_reqest_accepted,
    notify_speaker_reqest_declined,
)


# create a speaker request
@extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
class CreateSpeakerRequestView(APIView):
    """Create a speaker request."""

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """Create a speaker request."""
        serializer = SpeakerRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            notify_speaker_of_org_request(serializer.instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def get(self, request):
    #     """Get all speaker requests."""
    #     speaker_requests = SpeakerRequest.objects.all()
    #     serializer = SpeakerRequestSerializer(speaker_requests, many=True)
    #     return Response(serializer.data)


@extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
class SpeakerRequestsView(APIView):
    """Speaker request view.

    Retrieve, update, or delete a speaker request by speaker requested.
    Speaker can either accept or decline the request using this endpoint.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, speaker_slug: str) -> Response:
        """Get a speaker request by pk."""
        speaker_request = get_object_or_404(SpeakerRequest, speaker__slug=speaker_slug)
        if speaker_request.speaker.user_account != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to access this request.")
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data)

    def patch(self, request, speaker_slug: str) -> Response:
        """Update a speaker request by pk."""
        speaker_request = get_object_or_404(SpeakerRequest, speaker__slug=speaker_slug)
        if speaker_request.speaker.user_account != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to update this request.")
        serializer = SpeakerRequestAcceptDeclineSerializer(
            speaker_request, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if serializer.instance.status == RequestStatusChoices.ACCEPTED:
            notify_speaker_reqest_accepted(serializer.instance)
        elif serializer.instance.status == RequestStatusChoices.DECLINED:
            notify_speaker_reqest_declined(serializer.instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerRequestByOrganizationView(APIView):
    """Retrieve, update, or delete a speaker request based on organization."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer(many=True)
    )
    def get(self, request, org_slug: str) -> Response:
        """Get speaker requests by organization."""
        organization = get_object_or_404(Organization, slug=org_slug)
        self.check_object_permissions(request, organization)
        speaker_requests = SpeakerRequest.objects.filter(
            organization=organization
        ).select_related("speaker__user_account", "event", "requested_by")
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=OrganizationSpeakerRequestCancelSerializer,
        responses=SpeakerRequestSerializer,
    )
    def put(self, request, org_slug: str) -> Response:
        """Update a speaker request by organization.

        PUT in this endpoint is used to update the state of the request.
        """
        organization = get_object_or_404(Organization, slug=org_slug)
        self.check_object_permissions(request, organization)
        speaker_request = get_object_or_404(SpeakerRequest, organization=organization)
        serializer = OrganizationSpeakerRequestCancelSerializer(
            speaker_request, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer(many=True)
    )
    def patch(self, request, org_slug: str) -> Response:
        """Partially update a speaker request by organization."""
        organization = get_object_or_404(Organization, slug=org_slug)
        self.check_object_permissions(request, organization)
        speaker_request = get_object_or_404(SpeakerRequest, organization=organization)
        serializer = SpeakerRequestUpdateSerializer(
            speaker_request, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, org_slug: str) -> Response:
        """Delete a speaker request by organization."""
        organization = get_object_or_404(Organization, slug=org_slug)
        self.check_object_permissions(request, organization)
        speaker_request = get_object_or_404(SpeakerRequest, organization=organization)
        speaker_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpeakerRequestByRequestedSpeakerView(APIView):
    """Retrieve, update, or delete a speaker request by requested speaker."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def get(self, request, pk: UUID) -> Response:
        """Get a speaker request by requested speaker."""
        speaker_request = get_object_or_404(SpeakerRequest, pk=pk)
        if speaker_request.speaker.user_account != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to access this request.")
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data)

    @extend_schema(
        request=SpeakerRequestAcceptDeclineSerializer,
        responses=SpeakerRequestSerializer,
    )
    def put(self, request, pk: UUID) -> Response:
        """Update a speaker request by requested speaker."""
        speaker_request = get_object_or_404(SpeakerRequest, pk=pk)
        if speaker_request.speaker.user_account != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to update this request.")
        serializer = SpeakerRequestAcceptDeclineSerializer(
            speaker_request, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def patch(self, request, pk: UUID) -> Response:
        """Partially update a speaker request by requested speaker."""
        speaker_request = get_object_or_404(SpeakerRequest, pk=pk)
        if speaker_request.speaker.user_account != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to update this request.")
        serializer = SpeakerRequestSerializer(
            speaker_request, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk: UUID) -> Response:
        """Delete a speaker request by requested speaker."""
        speaker_request = get_object_or_404(SpeakerRequest, pk=pk)
        if speaker_request.speaker.user_account != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to delete this request.")
        speaker_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailSpeakerRequestView(APIView):
    """Request a speaker through email."""

    @extend_schema(
        request=EmailSpeakerRequestsSerializer, responses=EmailSpeakerRequestsSerializer
    )
    def post(self, request) -> Response:
        """Create a new email speaker request."""
        request.data["request_from"] = request.user
        serializer = EmailSpeakerRequestsSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            notify_speaker_email_request(serializer.instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses=EmailSpeakerRequestsSerializer(many=True))
    def get(self, request) -> Response:
        """List all email speaker requests."""
        email_speaker_requests = get_object_or_404(
            SpeakerEmailRequests, request_from=request.user
        )
        serializer = EmailSpeakerRequestsSerializer(email_speaker_requests, many=True)
        return Response(serializer.data)
