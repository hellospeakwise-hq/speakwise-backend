"""speakers app views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny

from speakers.models import SpeakerProfile
from speakers.serializers import (
    SpeakerProfileSerializer,
    SpeakerSocialLinksSerializer,
)


@extend_schema(
    request=SpeakerProfileSerializer,
    responses=SpeakerProfileSerializer(many=True),
)
class SpeakerProfileListCreateView(ListCreateAPIView):
    """View to list and create speaker profiles.

    This view allows users to view a list of speaker profiles and create a new one.
    """

    queryset = SpeakerProfile.objects.all()
    serializer_class = SpeakerProfileSerializer
    permission_classes = [AllowAny]


@extend_schema(
    request=SpeakerSocialLinksSerializer, responses=SpeakerSocialLinksSerializer
)
class SpeakerProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a speaker profile.

    This view allows users to manage a specific speaker profile.
    """

    queryset = SpeakerProfile.objects.all()
    serializer_class = SpeakerProfileSerializer
