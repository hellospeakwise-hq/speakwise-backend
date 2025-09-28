"""speakers app views."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from base.permissions import IsSpeaker
from speakers.models import RequestSpeaker, SpeakerProfile
from speakers.serializers import (
    SpeakerProfileSerializer,
    SpeakerRequestSerializer,
    SpeakerSocialLinksSerializer,
)


@extend_schema(
    request=SpeakerProfileSerializer,
    responses=SpeakerProfileSerializer(many=True),
)
class SpeakerProfileListCreateView(ListCreateAPIView):
    """list create speaker profile view."""

    queryset = SpeakerProfile.objects.all()
    serializer_class = SpeakerProfileSerializer
    permission_classes = [AllowAny]


@extend_schema(
    request=SpeakerSocialLinksSerializer, responses=SpeakerSocialLinksSerializer
)
class SpeakerProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """list create speaker profile view."""

    queryset = SpeakerProfile.objects.all()
    serializer_class = SpeakerProfileSerializer

# use retrieve update on this view and to avoid unnecessary code.
class SpeakerRequestsListview(ListAPIView):
    """list speaker requests view."""

    permission_classes = [IsSpeaker]

    def get_object(self, pk=None):
        """Get request speaker objects."""
        try:
            return RequestSpeaker.objects.get(pk=pk)
        except RequestSpeaker.DoesNotExist() as err:
            raise Http404 from err

    @extend_schema(
        responses=SpeakerRequestSerializer(many=True), tags=["Speaker Requests"]
    )
    def get(self, request):
        """List speaker requests."""
        requests = RequestSpeaker.objects.filter(
            organizer__user_account=self.request.user
        ).order_by("-created_at")
        serializer = SpeakerSocialLinksSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses=SpeakerRequestSerializer(), tags=["Speaker Requests"])
    def patch(self, request, pk=None):
        """List speaker requests."""
        requests = self.get_object(pk=pk)
        serializer = SpeakerSocialLinksSerializer(requests, request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
