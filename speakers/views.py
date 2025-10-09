"""speakers app views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny

from speakers.models import SpeakerProfile
from speakers.serializers import SpeakerProfileSerializer, SpeakerSocialLinksSerializer


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
    request=SpeakerProfileSerializer, responses=SpeakerProfileSerializer
)
class SpeakerProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """list create speaker profile view."""

    queryset = SpeakerProfile.objects.all()
    serializer_class = SpeakerProfileSerializer
