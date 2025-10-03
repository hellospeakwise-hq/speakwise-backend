"""speaker request views."""

from django.http.response import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizer, IsSpeaker
from speakerrequests.models import SpeakerRequest
from speakerrequests.serializers import SpeakerRequestSerializer

from .utils import speaker_request_payload


class SpeakerRequestListView(APIView):
    """speaker request list view."""

    permission_classes = [IsOrganizer]

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
        serializer_data = speaker_request_payload(request.user, request.data)
        serializer = SpeakerRequestSerializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


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
    def get(self, request):
        """Get speaker requests."""
        speaker_requests = self.get_objects(request.user)
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SpeakerRequestSerializer, responses=SpeakerRequestSerializer)
    def patch(self, request, pk=None):
        """Update a speaker request."""
        speaker_request = SpeakerRequest.objects.get(
            pk=pk, speaker__user_account=request.user
        )
        serializer = SpeakerRequestSerializer(
            speaker_request, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
