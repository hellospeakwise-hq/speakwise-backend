"""speakers app views."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from speakers.models import SpeakerExperiences, SpeakerProfile, SpeakerSkillTag
from speakers.serializers import (
    SpeakerExperiencesSerializer,
    SpeakerProfileSerializer,
    SpeakerSkillTagSerializer,
)
from users.models import User


@extend_schema(
    request=SpeakerProfileSerializer,
    responses=SpeakerProfileSerializer,
    tags=["Speaker Profile"],
)
class SpeakerProfileListCreateView(APIView):
    """View to list and create speaker profiles."""

    permission_classes = [AllowAny]

    def get(self, request):
        """List all speaker profiles."""
        speaker_profiles = SpeakerProfile.objects.all()
        serializer = SpeakerProfileSerializer(speaker_profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new speaker profile."""
        serializer = SpeakerProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=SpeakerProfileSerializer,
    responses=SpeakerProfileSerializer,
    tags=["Speaker Profile"],
)
class SpeakerProfileRetrieveUpdateDestroyView(APIView):
    """View to retrieve, update, and delete a speaker profile.

    This view allows users to manage a specific speaker profile.
    """

    SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]

    def get_permissions(self):
        """Get permissions based on request method."""
        if self.request.method in self.SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        """Get speaker profile by ID."""
        try:
            return SpeakerProfile.objects.get(id=pk)
        except SpeakerProfile.DoesNotExist as err:
            raise Http404 from err

    def get(self, request, pk):
        """Retrieve a specific speaker profile by ID."""
        speaker_profile = self.get_object(pk)
        serializer = SpeakerProfileSerializer(speaker_profile)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update a specific speaker profile by ID."""
        speaker_profile = self.get_object(pk)
        serializer = SpeakerProfileSerializer(
            speaker_profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete a specific speaker profile by ID."""
        speaker_profile = self.get_object(pk)
        speaker_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=SpeakerExperiencesSerializer,
    responses=SpeakerExperiencesSerializer(many=True),
    tags=["Speaker Experiences"],
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
    request=SpeakerExperiencesSerializer,
    responses=SpeakerExperiencesSerializer,
    tags=["Speaker Experiences"],
)
class SpeakerExperiencesRetrieveUpdateDestroyView(APIView):
    """View to retrieve, update, and delete a speaker experience.

    This view allows users to manage a specific speaker experience.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk: int, speaker: User):
        """Get speaker experience by primary key and user."""
        try:
            return SpeakerExperiences.objects.get(pk=pk, speaker__user_account=speaker)
        except SpeakerExperiences.DoesNotExist as err:
            raise Http404 from err

    def get(self, request, pk: int) -> Response:
        """Retrieve a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        serializer = SpeakerExperiencesSerializer(speaker_experience)
        return Response(serializer.data)

    def patch(self, request, pk: int) -> Response:
        """Update a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        serializer = SpeakerExperiencesSerializer(
            speaker_experience, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk: int) -> Response:
        """Delete a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        speaker_experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    responses=SpeakerExperiencesSerializer(many=True), tags=["Speaker Experiences"]
)
class PublicSpeakerExperiencesListView(APIView):
    """View to list all speaker experiences."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        """List all speaker experiences."""
        speaker_experiences = SpeakerExperiences.objects.filter(speaker=pk)
        serializer = SpeakerExperiencesSerializer(speaker_experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=SpeakerSkillTagSerializer,
    responses=SpeakerSkillTagSerializer,
    tags=["Speaker Skill Tag"],
)
class SpeakerSkillTagListView(APIView):
    """speaker skills view."""

    permission_classes = [IsAuthenticated]

    def get_speaker(self, pk: int):
        """Get speaker by id."""
        try:
            return SpeakerProfile.objects.get(id=pk)
        except SpeakerProfile.DoesNotExist as err:
            raise Http404 from err

    def get(self, request, pk: int) -> Response:
        """Get skill tags of a speaker."""
        speaker = self.get_speaker(pk)
        skills = SpeakerSkillTag.objects.filter(speaker=speaker)
        serializer = SpeakerSkillTagSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk: int) -> Response:
        """Create a speaker skill tag."""
        speaker = self.get_speaker(pk)
        serializer = SpeakerSkillTagSerializer(
            data=request.data, context={"speaker": speaker}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=SpeakerSkillTagSerializer,
    responses=SpeakerSkillTagSerializer,
    tags=["Speaker Skill Tag"],
)
class SpeakerSkillTagDetailView(APIView):
    """speaker skills detail view."""

    def get_permissions(self):
        """Get permissions."""
        if self.request.method in ["POST", "GET", "PATCH"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_object(self, pk: int):
        """Get a speaker skill tag object."""
        try:
            return SpeakerSkillTag.objects.get(pk=pk)
        except SpeakerSkillTag.DoesNotExist as err:
            raise Http404 from err

    def get(self, request, pk: int = None) -> Response:
        """Get a speaker skill tag."""
        skill = self.get_object(pk)
        serializer = SpeakerSkillTagSerializer(skill)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk: int = None) -> Response:
        """Update a speaker skill tag object."""
        skill = self.get_object(pk)
        if skill.speaker == self.request.user:
            serializer = SpeakerSkillTagSerializer(data=skill, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, pk: int = None) -> Response:
        """Delete a speaker skill object."""
        skill = self.get_object(pk)
        if skill.speaker == self.request.user:
            skill.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"Err": "Cannot delete skill tag of another user"},
            status=status.HTTP_400_BAD_REQUEST,
        )
