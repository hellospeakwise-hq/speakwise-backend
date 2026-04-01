"""Speaker request views."""

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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

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
    EmailRequestsSerializer,
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
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
            )
            response_serializer = self.serializer_class(speaker_request)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
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
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
