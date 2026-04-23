"""speaker request views."""

from django.conf import settings
from django.db.models import Q
from django.http.response import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import OrganizationMembership
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.filters import EmailRequestsFilter, SpeakerRequestFilter
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.serializers import (
    EmailRequestsSerializer,
    SpeakerRequestSerializer,
)
from speakerrequests.utils import (
    send_request_accepted_email,
    send_request_declined_email,
    send_speaker_email_request_email,
    send_speaker_org_request_email,
)


class SpeakerRequestListView(APIView):
    """View to list and create speaker requests.

    This view allows organizers to list all their speaker requests and create new ones.
    """

    permission_classes = [AllowAny]
    serializer_class = SpeakerRequestSerializer

    def get_objects(self, organizer, organization_id=None):
        """Get speaker requests by organizer.

        Args:
            organizer: The user making the request
            organization_id: Optional organization ID to filter by
        """
        try:
            # If organization_id is provided, use it directly
            if organization_id:
                # Verify user is a member of this organization
                membership = OrganizationMembership.objects.filter(
                    user=organizer, organization_id=organization_id
                ).first()
                if membership:
                    return SpeakerRequest.objects.filter(organizer_id=organization_id)
                else:
                    return SpeakerRequest.objects.none()

            # Otherwise, get requests for all organizations the user is a member of
            memberships = OrganizationMembership.objects.filter(user=organizer)
            org_ids = memberships.values_list("organization_id", flat=True)
            return SpeakerRequest.objects.filter(organizer_id__in=org_ids)
        except Exception as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer(many=True))
    def get(self, request):
        """Get all speaker requests for the authenticated organizer.

        Args:
            request: The HTTP request object.

        Returns:
            Response: A list of speaker requests.
        """
        organization_id = request.GET.get("organization")
        speaker_requests = self.get_objects(request.user, organization_id)
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SpeakerRequestSerializer)
    def post(self, request):
        """Create a new speaker request.

        Args:
            request: The HTTP request object containing the speaker request data.

        Returns:
            Response: The created speaker request data.
        """
        serializer = SpeakerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check for duplicate request (same org, speaker, event)
        organizer = serializer.validated_data.get("organizer")
        speaker = serializer.validated_data.get("speaker")
        event = serializer.validated_data.get("event")

        if SpeakerRequest.objects.filter(
            organizer=organizer, speaker=speaker, event=event
        ).exists():
            return Response(
                {
                    "detail": "A speaker request for this speaker and event already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        req = serializer.instance
        speaker_user = req.speaker.user_account
        send_speaker_org_request_email.enqueue(
            speaker_email=speaker_user.email,
            speaker_name=speaker_user.first_name or speaker_user.username,
            organization_name=req.organizer.name,
            organizer_name=req.organizer.name,
            event_name=req.event.title,
            event_date=req.event.start_date_time.strftime("%B %-d, %Y") if req.event.start_date_time else "",
            message=req.message,
            request_id=req.id,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SPeakerRequestDetailView(APIView):
    """View to retrieve, update, and delete a specific speaker request.

    This view allows organizers to manage individual speaker requests.
    """

    permission_classes = [AllowAny]
    serializer_class = SpeakerRequestSerializer

    def get_object(self, pk, organizer):
        """Get object by pk."""
        try:
            return SpeakerRequest.objects.get(pk=pk)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer)
    def get(self, request, pk=None):
        """Retrieve a specific speaker request by ID.

        Args:
            request: The HTTP request object.
            pk: The primary key of the speaker request.

        Returns:
            Response: The speaker request data.
        """
        speaker_request = self.get_object(pk, request.user)
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def patch(self, request, pk=None):
        """Update a specific speaker request.

        Args:
            request: The HTTP request object containing the update data.
            pk: The primary key of the speaker request.

        Returns:
            Response: The updated speaker request data.
        """
        speaker_request = self.get_object(pk, request.user)
        serializer = SpeakerRequestSerializer(
            speaker_request, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, pk=None):
        """Delete a specific speaker request.

        Args:
            request: The HTTP request object.
            pk: The primary key of the speaker request.

        Returns:
            Response: HTTP 204 No Content.
        """
        speaker_request = self.get_object(pk, request.user)
        speaker_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpeakerRequestsListView(APIView):
    """View to list incoming speaker requests for a speaker.

    This view allows speakers to see all requests sent to them.
    """

    permission_classes = [AllowAny]

    def get_objects(self, speaker):
        """Get speaker requests by speaker."""
        try:
            return SpeakerRequest.objects.filter(speaker__user_account=speaker)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer(many=True))
    def get(self, request, pk=None):
        """Get all incoming speaker requests for the authenticated speaker.

        Args:
            request: The HTTP request object.
            pk: Ignored.

        Returns:
            Response: A list of incoming speaker requests.
        """
        speaker_requests = self.get_objects(request.user)
        speaker_requests_filter = SpeakerRequestFilter(
            request.GET, queryset=speaker_requests
        )
        serializer = SpeakerRequestSerializer(speaker_requests_filter.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerRequestAcceptView(APIView):
    """View to accept or decline a speaker request.

    This view allows speakers to respond to a request.
    """

    permission_classes = [AllowAny]

    def get_object(self, pk, user):
        """Get object by pk and ensure it belongs to the speaker."""
        try:
            return SpeakerRequest.objects.get(pk=pk, speaker__user_account=user)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def patch(self, request, pk=None):
        """Respond to a speaker request (accept or decline).

        Args:
            request: The HTTP request object containing the status update.
            pk: The primary key of the speaker request.

        Returns:
            Response: The updated speaker request data.
        """
        speaker_request = self.get_object(pk, request.user)
        current_status = speaker_request.status
        if current_status != RequestStatusChoices.PENDING.value:
            return Response(
                {"detail": "You can only update requests that are in PENDING status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SpeakerRequestSerializer(
            speaker_request, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        req = serializer.instance
        speaker_user = req.speaker.user_account
        speaker_name = speaker_user.first_name or speaker_user.username
        organizer_email = req.organizer.email
        requester_name = req.organizer.name
        event_name = req.event.title
        event_date = req.event.start_date_time.strftime("%B %-d, %Y") if req.event.start_date_time else ""
        event_location = req.event.location.name if req.event.location else ""
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


@extend_schema(
    request=EmailRequestsSerializer,
    responses=EmailRequestsSerializer,
    tags=["speaker email-request"],
)
class SpeakerEmailRequestListView(APIView):
    """Speaker request sent via email."""

    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        """Get email requests sent or received by the user."""
        try:
            return SpeakerEmailRequests.objects.filter(
                Q(request_from=user) | Q(request_to=user)
            )
        except SpeakerEmailRequests.DoesNotExist:
            return NotFound

    def get(self, request):
        """Return request sent or received by the authenticated user."""
        email_requests = self.get_object(request.user)
        email_request_filter = EmailRequestsFilter(request.GET, queryset=email_requests)
        serializer = EmailRequestsSerializer(email_request_filter.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new request sent via email."""
        # reconstruct request data
        speaker_id = request.data.get("speaker_id")
        if not speaker_id:
            return Response(
                {"speaker_id": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.data["request_to"] = speaker_id
        request.data["request_from"] = request.user.id

        # validate and save request data
        serializer = EmailRequestsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # send the request via email if the recipient exists
        if serializer.instance.request_to:
            er = serializer.instance
            recipient = er.request_to
            sender = er.request_from
            send_speaker_email_request_email.enqueue(
                speaker_email=recipient.email,
                speaker_name=recipient.first_name or recipient.username,
                requester_name=sender.first_name or sender.username,
                requester_email=sender.email,
                event_name=er.event,
                event_location=er.location,
                message=er.message,
                request_id=str(er.id),
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=EmailRequestsSerializer,
    responses={200: None},
    tags=["speaker email-request"],
)
class SpeakerEmailRequestDetailView(APIView):
    """Detail view of Speaker request sent through email."""

    def patch(self, request, pk=None):
        """Update status of a specific speaker request."""
        email_request = get_object_or_404(
            SpeakerEmailRequests,
            pk=pk,
            request_to=request.user,
        )
        new_status = request.data.get("status")
        if new_status != email_request.status:
            email_request.status = new_status
            email_request.save()
            return Response(
                EmailRequestsSerializer(email_request).data,
                status=status.HTTP_200_OK,
            )
        return Response(status=status.HTTP_200_OK)
