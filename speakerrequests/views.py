"""Speaker request views."""

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
=======
from django.db.models import Q
from django.http.response import Http404
>>>>>>> 46e772f (work in progres)
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
=======
from rest_framework import generics, status
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
from rest_framework import status
>>>>>>> 7255978 (refactor speakerrequest API)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

<<<<<<< HEAD
<<<<<<< HEAD
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
=======
from speakerrequests.models import SpeakerRequest, SpeakerEmailRequests
from speakerrequests.serializers import (
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
    SpeakerRequestSerializer,
=======
from base.permissions import IsOrganizationAdminOrOrganizer, IsSpeakerRequestRecipient
from speakerrequests.filters import EmailRequestsFilter, SpeakerRequestFilter
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.serializers import (
>>>>>>> 7255978 (refactor speakerrequest API)
    EmailRequestsSerializer,
    SpeakerRequestSerializer,
)
<<<<<<< HEAD
<<<<<<< HEAD
from speakerrequests.services import SpeakerRequestService
=======
from speakerrequests.utils import (
    send_request_accepted_email,
    send_speaker_request_declined_email,
    send_speaker_request_email,
)
>>>>>>> 46e772f (work in progres)


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

<<<<<<< HEAD
        speaker_request = SpeakerRequestService.create_request(
            organizer=organizer,
            speaker=serializer.validated_data["speaker"],
            event=event,
            message=serializer.validated_data["message"],
        )
        return Response(
            SpeakerRequestSerializer(speaker_request).data,
            status=status.HTTP_201_CREATED,
=======
        # send email notification to speaker
        send_speaker_request_email.enqueue(
            speaker_email=serializer.instance.speaker.user_account.email,
            event_name=serializer.instance.event.title,
            organizer_name=serializer.instance.organizer.name,
            message=serializer.instance.message,
>>>>>>> 46e772f (work in progres)
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
<<<<<<< HEAD

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
=======
        serializer.save()
        # send email notification to speaker if request is accepted or declined
        (
>>>>>>> 46e772f (work in progres)
            send_request_accepted_email.enqueue(
                speaker=serializer.instance.speaker,
                _event=serializer.instance.event,
            )
            if serializer.instance.status == RequestStatusChoices.ACCEPTED.value
            else send_speaker_request_declined_email.enqueue(
                speaker_email=serializer.instance.speaker,
                event_name=serializer.instance.event,
            )
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

<<<<<<< HEAD
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
=======
        # send the request via email if the recipient exists
        if serializer.instance.request_to:
            send_speaker_request_email.enqueue(
                speaker_email=serializer.instance.request_to.email,
                event_name=serializer.instance.event,
                organizer_name=serializer.instance.request_from.username,
                message=serializer.instance.message,
=======
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

<<<<<<< HEAD
        try:
            speaker_request = SpeakerRequestService.create_request(
                organizer=request.user,
                speaker=serializer.validated_data["speaker"],
                event=serializer.validated_data["event"],
                message=serializer.validated_data["message"],
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
            )
            response_serializer = self.serializer_class(speaker_request)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
=======
        # create speaker request
        speaker_request = SpeakerRequestService.create_request(
            organizer=serializer.validated_data["organizer"],
            speaker=serializer.validated_data["speaker"],
            event=serializer.validated_data["event"],
            message=serializer.validated_data["message"],
        )
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
>>>>>>> 7255978 (refactor speakerrequest API)


class OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView(APIView):
    """View for organizers to manage individual speaker requests."""

<<<<<<< HEAD
    def patch(self, request, pk=None):
        """Update status of a specific speaker request."""
        email_request = get_object_or_404(
            SpeakerEmailRequests,
            pk=pk,
            request_to=request.user,
>>>>>>> 46e772f (work in progres)
        )
=======
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

<<<<<<< HEAD
    def get_queryset(self):
        """Ensure user is the recipient if they are updating status."""
        return SpeakerEmailRequests.objects.filter(request_to=self.request.user)
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
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
>>>>>>> 7255978 (refactor speakerrequest API)
