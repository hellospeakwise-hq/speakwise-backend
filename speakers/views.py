"""speakers app views."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from speakers.models import SpeakerExperiences, SpeakerProfile
from speakers.serializers import (
    SpeakerExperiencesSerializer,
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


@extend_schema(
    request=SpeakerExperiencesSerializer,
    responses=SpeakerExperiencesSerializer(many=True),
)
class SpeakerExperiencesListCreateView(APIView):
    """View to list and create speaker experiences.

    This view allows users to view a list of speaker experiences and create a new one.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all speaker experiences for the authenticated user."""
        speaker_experiences = SpeakerExperiences.objects.filter(
            speaker__user_account=request.user
        )
        serializer = SpeakerExperiencesSerializer(speaker_experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new speaker experience for the authenticated user."""
        serializer = SpeakerExperiencesSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=SpeakerExperiencesSerializer, responses=SpeakerExperiencesSerializer
)
class SpeakerExperiencesRetrieveUpdateDestroyView(APIView):
    """View to retrieve, update, and delete a speaker experience.

    This view allows users to manage a specific speaker experience.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, speaker):
        """Get speaker experience by primary key and user."""
        try:
            return SpeakerExperiences.objects.get(pk=pk, speaker__user_account=speaker)
        except SpeakerExperiences.DoesNotExist as err:
            raise Http404 from err

    def get(self, request, pk):
        """Retrieve a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        serializer = SpeakerExperiencesSerializer(speaker_experience)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        serializer = SpeakerExperiencesSerializer(
            speaker_experience, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        speaker_experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
