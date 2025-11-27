"""speaker request views."""

from django.http.response import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest
from speakerrequests.serializers import SpeakerRequestSerializer
from speakerrequests.utils import (
    send_request_accepted_email,
    send_speaker_request_declined_email,
    send_speaker_request_email,
)


class SpeakerRequestListView(APIView):
    """View to list and create speaker requests.

    This view allows organizers to list all their speaker requests and create new ones.
    """

    permission_classes = [AllowAny]

    def get_objects(self, organizer):
        """Get speaker requests by organizer."""
        try:
            return SpeakerRequest.objects.filter(organizer__user_account=organizer)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer(many=True))
    def get(self, request):
        """Get all speaker requests for the authenticated organizer.

        Args:
            request: The HTTP request object.

        Returns:
            Response: A list of speaker requests.
        """
        speaker_requests = self.get_objects(request.user)
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
        serializer.save()

        # send email notification to speaker
        send_speaker_request_email(
            speaker_email=serializer.instance.speaker.user_account.email,
            event_name=serializer.instance.event.title,
            organizer_name=serializer.instance.organizer.user_account.username,
            message=serializer.instance.message,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SPeakerRequestDetailView(APIView):
    """View to retrieve, update, and delete a specific speaker request.

    This view allows organizers to manage individual speaker requests.
    """

    permission_classes = [AllowAny]

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
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
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
        # send email notification to speaker if request is accepted or declined
        (
            send_request_accepted_email(
                speaker_email=serializer.instance.speaker.user_account.email,
                event_name=serializer.instance.event.title,
                speaker_name=serializer.instance.speaker.user_account.email,
            )
            if serializer.instance.status == RequestStatusChoices.ACCEPTED.value
            else send_speaker_request_declined_email(
                speaker_email=serializer.instance.speaker.user_account.email,
                event_name=serializer.instance.event.title,
                speaker_name=serializer.instance.speaker.user_account.email,
            )
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
