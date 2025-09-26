"""speakers app views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from speakers.models import SpeakerProfile, RequestSpeaker
from speakers.serializers import SpeakerProfileSerializer, SpeakerSocialLinksSerializer, RequestSpeakerSerializer


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
    @extend_schema(
        responses=RequestSpeakerSerializer(many=True) )
    def get(self, request):
        """requested speakers."""
        serializer = SpeakerSocialLinksSerializer(RequestSpeaker.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @extend_schema(
        request=RequestSpeakerSerializer,responses=RequestSpeakerSerializer )
    def post(self, request):
        """request speaker."""
        serializer = SpeakerSocialLinksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # send speaker an email
        return Response(serializer.data, status=status.HTTP_201_CREATED)
