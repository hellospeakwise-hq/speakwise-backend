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
from speakers.models import  SpeakerProfile
from speakers.serializers import (
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

