"""Speaker request views."""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer, IsSpeakerRequestRecipient
from organizations.models import OrganizationMembership
from speakerrequests.filters import EmailRequestsFilter, SpeakerRequestFilter
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.serializers import (
    EmailRequestCreateSerializer,
    EmailRequestsRespondSerializer,
    EmailRequestsSerializer,
    SpeakerRequestCreateSerializer,
    SpeakerRequestRespondSerializer,
    SpeakerRequestSerializer,
)
from speakerrequests.services import SpeakerRequestService


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrganizerSpeakerRequestListCreateAPIView(APIView):
    """View for organizers to list and create speaker requests."""

    permission_classes = [IsAuthenticated, IsOrganizationAdminOrOrganizer]

    def get_queryset(self):
        """Filter requests for organizations where the user is an admin/organizer."""
        return SpeakerRequest.objects.for_organizer(self.request.user).with_prefetches()

    @extend_schema(responses={200: SpeakerRequestSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List speaker requests."""
        queryset = self.get_queryset()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = SpeakerRequestSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SpeakerRequestSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=SpeakerRequestCreateSerializer,
        responses={201: SpeakerRequestSerializer},
    )
    def post(self, request, *args, **kwargs):
        """Create a new speaker request."""
        serializer = SpeakerRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = serializer.validated_data["event"]
        organizer = event.organizer

        if not organizer:
            raise serializers.ValidationError(
                {"event": "This event has no associated organizer."}
            )

        # Ensure the user is an admin/organizer of this organization
        if not OrganizationMembership.objects.filter(
            organization=organizer,
            user=self.request.user,
            role__in=["ADMIN", "ORGANIZER"],
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                {
                    "detail": "You do not have permission to create requests for this organization."
                }
            )

        speaker_request = SpeakerRequestService.create_request(
            organizer=organizer,
            speaker=serializer.validated_data["speaker"],
            event=event,
            message=serializer.validated_data["message"],
        )
        return Response(
            SpeakerRequestSerializer(speaker_request).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView(APIView):
    """View for organizers to retrieve, update, and delete speaker requests."""

    permission_classes = [IsAuthenticated, IsOrganizationAdminOrOrganizer]

    def get_object(self, pk):
        """Get object and check permissions."""
        obj = get_object_or_404(SpeakerRequest, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(responses={200: SpeakerRequestSerializer})
    def get(self, request, pk, *args, **kwargs):
        """Retrieve a speaker request."""
        speaker_request = self.get_object(pk)
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data)

    @extend_schema(
        request=SpeakerRequestSerializer, responses={200: SpeakerRequestSerializer}
    )
    def patch(self, request, pk, *args, **kwargs):
        """Update a speaker request."""
        speaker_request = self.get_object(pk)
        serializer = SpeakerRequestSerializer(
            speaker_request, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses={204: None})
    def delete(self, request, pk, *args, **kwargs):
        """Delete a speaker request."""
        speaker_request = self.get_object(pk)
        speaker_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpeakerRequestRespondAPIView(APIView):
    """View for speakers to respond to requests."""

    permission_classes = [IsAuthenticated, IsSpeakerRequestRecipient]

    def get_object(self, pk):
        """Get object and check permissions."""
        obj = get_object_or_404(SpeakerRequest, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        request=SpeakerRequestRespondSerializer, responses=SpeakerRequestSerializer
    )
    def patch(self, request, pk, *args, **kwargs):
        """Allow a speaker to respond to a specific request."""
        speaker_request = self.get_object(pk)

        serializer = SpeakerRequestRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_request = SpeakerRequestService.respond_to_request(
            speaker_request=speaker_request,
            status_update=serializer.validated_data["status"],
        )
        return Response(
            SpeakerRequestSerializer(updated_request).data, status=status.HTTP_200_OK
        )
<<<<<<< HEAD
=======
        event_location = req.event.location.venue if req.event.location else ""
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard/organizer"
        speaker_profile_url = f"{settings.FRONTEND_URL}/speakers/{req.speaker.id}"
        discover_url = f"{settings.FRONTEND_URL}/speakers"

        if req.status == RequestStatusChoices.ACCEPTED.value:
            send_request_accepted_email.enqueue(
                organizer_email=organizer_email,
                requester_name=requester_name,
                speaker_name=speaker_name,
                speaker_title="",
                event_name=event_name,
                event_date=event_date,
                event_location=event_location,
                speaker_profile_url=speaker_profile_url,
                dashboard_url=dashboard_url,
            )
        else:
            send_request_declined_email.enqueue(
                organizer_email=organizer_email,
                requester_name=requester_name,
                speaker_name=speaker_name,
                event_name=event_name,
                discover_url=discover_url,
            )
        return Response(serializer.data, status=status.HTTP_200_OK)
>>>>>>> 6cedfed (fix: use location.venue and set console log level to WARNING)


class SpeakerEmailRequestListCreateAPIView(APIView):
    """View for managing email-based speaker requests."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter email requests for the current user."""
        return SpeakerEmailRequests.objects.filter(
            request_to=self.request.user
        ).select_related("request_from", "request_to")

    @extend_schema(responses={200: EmailRequestsSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List email requests."""
        queryset = self.get_queryset()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = EmailRequestsSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = EmailRequestsSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=EmailRequestCreateSerializer, responses={201: EmailRequestsSerializer}
    )
    def post(self, request, *args, **kwargs):
        """Create a new email request."""
        serializer = EmailRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_request = SpeakerRequestService.create_email_request(
            request_from=self.request.user,
            request_to_user=serializer.validated_data["request_to"],
            event=serializer.validated_data["event"],
            message=serializer.validated_data["message"],
        )
        return Response(
            EmailRequestsSerializer(email_request).data, status=status.HTTP_201_CREATED
        )


class SpeakerEmailRequestRespondAPIView(APIView):
    """View for responding to email requests."""

    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        """Get object and check ownership."""
        obj = get_object_or_404(
            SpeakerEmailRequests, id=id, request_to=self.request.user
        )
        return obj

    @extend_schema(
        request=EmailRequestsRespondSerializer, responses=EmailRequestsSerializer
    )
    def patch(self, request, id, *args, **kwargs):
        """Allow a user to respond to a specific email request."""
        email_request = self.get_object(id)
        serializer = EmailRequestsRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_email_request = SpeakerRequestService.respond_to_email_request(
            email_request=email_request,
            status_update=serializer.validated_data["status"],
        )
        return Response(
            EmailRequestsSerializer(updated_email_request).data,
            status=status.HTTP_200_OK,
        )
