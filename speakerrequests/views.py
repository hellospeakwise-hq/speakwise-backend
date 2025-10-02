"""speaker request views."""
from django.http.response import Http404

from speakerrequests.models import SpeakerRequest
from speakerrequests.serializers import SpeakerRequestSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from base.permissions import IsOrganizer


class SpeakerRequestListView(APIView):
    """speaker request list view."""
    permission_classes = [IsOrganizer]
    def get_objects(self, organizer):
        try:
            return SpeakerRequest.objects.filter(organizer__user_account=organizer)
        except SpeakerRequest.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerRequestSerializer(many=True))
    def get(self, request):
        """get speaker requests."""
        speaker_requests = self.get_objects(request.user)
        serializer = SpeakerRequestSerializer(speaker_requests, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
