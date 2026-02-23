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

from speakers.models import (
    SpeakerExperiences,
    SpeakerFollow,
    SpeakerProfile,
    SpeakerSkillTag,
)
from speakers.serializers import (
    SpeakerExperiencesSerializer,
    SpeakerFollowSerializer,
    SpeakerProfileSerializer,
    SpeakerSkillTagSerializer,
)
from users.models import User


class SpeakerProfileListCreateView(APIView):
    """View to list and create speaker profiles."""

    permission_classes = [AllowAny]

    @extend_schema(responses=SpeakerProfileSerializer(many=True))
    def get(self, request):
        """List all speaker profiles."""
        speaker_profiles = SpeakerProfile.objects.all()
        serializer = SpeakerProfileSerializer(
            speaker_profiles, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=SpeakerProfileSerializer, responses=SpeakerProfileSerializer)
    def post(self, request):
        """Create a new speaker profile."""
        serializer = SpeakerProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(request=SpeakerProfileSerializer, responses=SpeakerProfileSerializer)
class SpeakerProfileRetrieveUpdateDestroyView(APIView):
    """View to retrieve, update, and delete a speaker profile.

    This view allows users to manage a specific speaker profile.
    """

    SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]
    lookup_field = "slug"

    def get_permissions(self):
        """Get permissions based on request method."""
        if self.request.method in self.SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, slug: str):
        """Get speaker profile by ID."""
        try:
            return SpeakerProfile.objects.get(slug=slug)
        except SpeakerProfile.DoesNotExist as err:
            raise Http404 from err

    def get(self, request, slug: str):
        """Retrieve a specific speaker profile by ID."""
        speaker_profile = self.get_object(slug)
        serializer = SpeakerProfileSerializer(
            speaker_profile, context={"request": request}
        )
        return Response(serializer.data)

    def patch(self, request, slug: str):
        """Update a specific speaker profile by ID."""
        speaker_profile = self.get_object(slug)
        serializer = SpeakerProfileSerializer(
            speaker_profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug: str):
        """Delete a specific speaker profile by ID."""
        speaker_profile = self.get_object(slug)
        speaker_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=SpeakerExperiencesSerializer,
    responses=SpeakerExperiencesSerializer(many=True),
    tags=["speaker experiences"],
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
    tags=["speaker experiences"],
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


class PublicSpeakerExperiencesListView(APIView):
    """Public view to list experiences for a given speaker slug."""

    permission_classes = [AllowAny]

    @extend_schema(
        responses=SpeakerExperiencesSerializer(many=True),
        tags=["speaker experiences (public view)"],
    )
    def get(self, request, slug: str = None):
        """List all speaker experiences for the provided speaker slug.

        If the slug does not match any speaker, an empty list is returned.
        """
        speaker_experiences = SpeakerExperiences.objects.filter(speaker__slug=slug)
        serializer = SpeakerExperiencesSerializer(speaker_experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["speaker experiences (private view)"],
)
class PrivateSpeakerExperienceListView(APIView):
    """View to list all speaker experiences."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=SpeakerExperiencesSerializer(many=True),
        request=SpeakerExperiencesSerializer,
    )
    def post(self, request):
        """Create a new speaker experience for the authenticated user."""
        serializer = SpeakerExperiencesSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["speaker experiences (private view)"])
class PrivateSpeakerExperienceRetrieveUpdateDestroyView(APIView):
    """View to retrieve, update, and delete a speaker experience."""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk: int, speaker: User):
        """Get speaker experience by primary key and user."""
        try:
            return SpeakerExperiences.objects.get(pk=pk, speaker__user_account=speaker)
        except SpeakerExperiences.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerExperiencesSerializer)
    def get(self, request, pk: int) -> Response:
        """Retrieve a specific speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        serializer = SpeakerExperiencesSerializer(speaker_experience)
        return Response(serializer.data)

    @extend_schema(responses=SpeakerExperiencesSerializer)
    def patch(self, request, pk: int) -> Response:
        """Update a speaker experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        serializer = SpeakerExperiencesSerializer(
            speaker_experience, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: None})
    def delete(self, request, pk: int) -> Response:
        """Delete a speaker's experience by ID."""
        speaker_experience = self.get_object(pk, request.user)
        speaker_experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["speaker skill tags"])
class SpeakerSkillTagsListView(APIView):
    """List and create skill tags for the authenticated user's speaker profile."""

    permission_classes = [IsAuthenticated]

    def get_objects(self, user: User):
        """Return all skill tags for the given user's speaker profile."""
        return SpeakerSkillTag.objects.filter(speaker__user_account=user)

    @extend_schema(
        responses=SpeakerSkillTagSerializer(many=True),
        request=SpeakerSkillTagSerializer,
    )
    def get(self, request):
        """List all skill tags for the authenticated user."""
        skill_tags = self.get_objects(request.user)
        serializer = SpeakerSkillTagSerializer(skill_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses=SpeakerSkillTagSerializer, request=SpeakerSkillTagSerializer
    )
    def post(self, request):
        """Create a new skill tag for the authenticated user's speaker profile."""
        serializer = SpeakerSkillTagSerializer(data=request.data)
        if serializer.is_valid():
            speaker_profile = request.user.speakers_profile_user.first()
            if speaker_profile is None:
                return Response(
                    {"detail": "Speaker profile not found for user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save(speaker=speaker_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["speaker skill tags"])
class SpeakerSkillTagsDetailView(APIView):
    """Retrieve, update, and delete a skill tag owned by the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk: int, speaker: User):
        """Get a speaker skill tag by primary key and user."""
        try:
            return SpeakerSkillTag.objects.get(pk=pk, speaker__user_account=speaker)
        except SpeakerSkillTag.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerSkillTagSerializer)
    def get(self, request, pk: int) -> Response:
        """Retrieve a specific speaker skill tag by primary key and user."""
        speaker_skill_tag = self.get_object(pk, request.user)
        serializer = SpeakerSkillTagSerializer(speaker_skill_tag)
        return Response(serializer.data)

    @extend_schema(
        responses=SpeakerSkillTagSerializer, request=SpeakerSkillTagSerializer
    )
    def patch(self, request, pk: int) -> Response:
        """Update a specific speaker skill tag by primary key and user."""
        speaker_skill_tag = self.get_object(pk, request.user)
        serializer = SpeakerSkillTagSerializer(
            speaker_skill_tag, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: None})
    def delete(self, request, pk: int) -> Response:
        """Delete a specific speaker skill tag by primary key and user."""
        speaker_skill_tag = self.get_object(pk, request.user)
        speaker_skill_tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["speaker follow"])
class SpeakerFollowView(APIView):
    """Follow, unfollow, or check follow status for a speaker.

    POST   /speakers/<slug>/follow/  → follow
    DELETE /speakers/<slug>/follow/  → unfollow
    GET    /speakers/<slug>/follow/  → check if authenticated user follows this speaker
    """

    permission_classes = [IsAuthenticated]

    def get_speaker(self, slug: str) -> SpeakerProfile:
        """Get speaker profile by slug."""
        try:
            return SpeakerProfile.objects.get(slug=slug)
        except SpeakerProfile.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "is_following": {"type": "boolean"},
                    "followers_count": {"type": "integer"},
                },
            }
        },
    )
    def get(self, request, slug: str) -> Response:
        """Check if the authenticated user is following this speaker."""
        speaker = self.get_speaker(slug)
        is_following = SpeakerFollow.objects.filter(
            follower=request.user, speaker=speaker
        ).exists()
        return Response(
            {"is_following": is_following, "followers_count": speaker.followers_count},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={
            201: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "followers_count": {"type": "integer"},
                },
            },
        },
    )
    def post(self, request, slug: str) -> Response:
        """Follow a speaker. Returns 201 on success, 400 if already following."""
        speaker = self.get_speaker(slug)
        if speaker.user_account == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = SpeakerFollow.objects.get_or_create(
            follower=request.user, speaker=speaker
        )
        if not created:
            return Response(
                {"detail": "You are already following this speaker."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "detail": "Successfully followed speaker.",
                "followers_count": speaker.followers_count,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "followers_count": {"type": "integer"},
                },
            }
        },
    )
    def delete(self, request, slug: str) -> Response:
        """Unfollow a speaker. Returns 200 on success, 400 if not following."""
        speaker = self.get_speaker(slug)
        deleted_count, _ = SpeakerFollow.objects.filter(
            follower=request.user, speaker=speaker
        ).delete()
        if deleted_count == 0:
            return Response(
                {"detail": "You are not following this speaker."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "detail": "Successfully unfollowed speaker.",
                "followers_count": speaker.followers_count,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["speaker follow"])
class SpeakerFollowersListView(APIView):
    """List all followers for a given speaker (public)."""

    permission_classes = [AllowAny]

    def get_speaker(self, slug: str) -> SpeakerProfile:
        """Get speaker profile by slug."""
        try:
            return SpeakerProfile.objects.get(slug=slug)
        except SpeakerProfile.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=SpeakerFollowSerializer(many=True))
    def get(self, request, slug: str) -> Response:
        """List all users following the given speaker."""
        speaker = self.get_speaker(slug)
        follows = SpeakerFollow.objects.filter(speaker=speaker).select_related(
            "follower"
        )
        serializer = SpeakerFollowSerializer(follows, many=True)
        return Response(
            {"followers_count": speaker.followers_count, "followers": serializer.data},
            status=status.HTTP_200_OK,
        )
