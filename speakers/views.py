"""speakers app views."""

from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from speakers.models import SpeakerExperiences, SpeakerProfile
from speakers.serializers import (
    SpeakerExperiencesSerializer,
    SpeakerProfileSerializer,
)


class SpeakerProfileListCreateView(ListCreateAPIView):
    """View to list and create speaker profiles."""

    permission_classes = [AllowAny]
    queryset = SpeakerProfile.objects.all().select_related("user_account")
    serializer_class = SpeakerProfileSerializer


class SpeakerProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a speaker profile."""

    queryset = SpeakerProfile.objects.all().select_related("user_account")
    serializer_class = SpeakerProfileSerializer

    def get_permissions(self):
        """Get permissions based on request method."""
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [AllowAny()]
        return [IsAuthenticated()]


class SpeakerExperiencesListCreateView(ListCreateAPIView):
    """View to list and create speaker experiences."""

    permission_classes = [IsAuthenticated]
    serializer_class = SpeakerExperiencesSerializer

    def get_queryset(self):
        """List all speaker experiences for the authenticated user."""
        return SpeakerExperiences.objects.filter(
            speaker__user_account=self.request.user
        ).select_related("speaker")


class SpeakerExperiencesRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a speaker experience."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SpeakerExperiencesSerializer

    def get_queryset(self):
        """Get speaker experiences for the user."""
        if self.request.user.is_authenticated:
            return SpeakerExperiences.objects.filter(
                speaker__user_account=self.request.user
            ).select_related("speaker")
        return SpeakerExperiences.objects.none()


class PublicSpeakerExperiencesListView(ListAPIView):
    """View to list all speaker experiences for a specific speaker."""

    permission_classes = [AllowAny]
    serializer_class = SpeakerExperiencesSerializer

    def get_queryset(self):
        """List all speaker experiences for a given speaker ID."""
        return SpeakerExperiences.objects.filter(
            speaker_id=self.kwargs["pk"]
        ).select_related("speaker")
