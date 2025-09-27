"""speakers app views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizer
from speakers.models import RequestSpeaker, SpeakerProfile
from speakers.serializers import (
    RequestSpeakerSerializer,
    SpeakerProfileSerializer,
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


class RequestSpeakerView(APIView):
    """request speaker view."""

    permission_classes = [IsOrganizer]

    @extend_schema(responses=RequestSpeakerSerializer(many=True))
    def get(self, request):
        """Requested speakers."""
        # request should be filtered based on organizer.
        serializer = SpeakerSocialLinksSerializer(
            RequestSpeaker.objects.filter(organizer__user_account=self.request.user),
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=RequestSpeakerSerializer, responses=RequestSpeakerSerializer)
    def post(self, request):
        """Request speaker."""
        serializer = SpeakerSocialLinksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # send speaker an email
        return Response(serializer.data, status=status.HTTP_201_CREATED)
