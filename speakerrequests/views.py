"""speaker request views."""

from django.http.response import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsAdminOrOrganizer, IsOrganizer, IsSpeaker
from organizers.models import OrganizerProfile
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest
from speakerrequests.serializers import SpeakerRequestSerializer
from speakerrequests.utils import (
    send_request_accepted_email,
    send_speaker_request_declined_email,
    send_speaker_request_email,
)


class SpeakerRequestListView(APIView):
    """speaker request list view."""

    permission_classes = [IsAdminOrOrganizer]

    def get_objects(self, organizer):
        """Get speaker requests by organizer."""
        try:
            return SpeakerRequest.objects.filter(organizer__user_account=organizer)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer(many=True))
    def get(self, request):
        """Get speaker requests."""
        speaker_requests = self.get_objects(request.user)
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SpeakerRequestSerializer)
    def post(self, request):
        """Create a speaker request."""
        organizer_profile = OrganizerProfile.objects.get(user_account=request.user).pk
        print("ORGANIZER PROFILE", organizer_profile)
        serializer_data = {
            "event": request.data.get("event"),
            "organizer": organizer_profile,
            "speaker": request.data.get("speaker"),
            "status": request.data.get("status", RequestStatusChoices.PENDING.value),
            "message": request.data.get("message", ""),
        }

        serializer = SpeakerRequestSerializer(data=serializer_data)
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
    """speaker request detail view."""

    permission_classes = [IsOrganizer]

    def get_object(self, pk, organizer):
        """Get object by pk."""
        try:
            return SpeakerRequest.objects.get(pk=pk, organizer__user_account=organizer)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer)
    def get(self, request, pk=None):
        """Get a speaker request."""
        speaker_request = self.get_object(pk, request.user)
        serializer = SpeakerRequestSerializer(speaker_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def patch(self, request, pk=None):
        """Update a speaker request."""
        speaker_request = self.get_object(pk, request.user)
        serializer = SpeakerRequestSerializer(
            speaker_request, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, pk=None):
        """Delete a speaker request."""
        speaker_request = self.get_object(pk, request.user)
        speaker_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpeakerRequestsListView(APIView):
    """list request of a speaker."""

    permission_classes = [IsSpeaker]

    def get_objects(self, speaker):
        """Get speaker requests by speaker."""
        try:
            return SpeakerRequest.objects.filter(speaker__user_account=speaker)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer(many=True))
    def get(self, request, pk=None):
        """Get speaker requests."""
        speaker_requests = self.get_objects(request.user)
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerRequestAcceptView(APIView):
    """accept or decline a speaker request."""

    permission_classes = [IsSpeaker]

    def get_object(self, pk, user):
        """Get object by pk and ensure it belongs to the speaker."""
        try:
            return SpeakerRequest.objects.get(pk=pk, speaker__user_account=user)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def patch(self, request, pk=None):
        """Update a speaker request."""
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
