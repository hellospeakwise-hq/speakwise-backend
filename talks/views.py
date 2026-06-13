"""talks views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from talks.filters import TalksFilter
from talks.models import TalkReviewComment, Talks
from talks.serializers import TalkReviewCommentSerializer, TalkSerializer


@extend_schema(request=TalkSerializer, responses=TalkSerializer)
class TalkListCreateView(APIView):
    """list and create view for talks."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(responses={200: TalkSerializer(many=True)})
    def get(self, request):
        """List talks."""
        qs = Talks.objects.select_related(
            "speaker__user_account", "event"
        ).prefetch_related("talk_sessions")
        if request.user.is_authenticated:
            qs = qs.filter(speaker__user_account=request.user)
        else:
            qs = Talks.objects.none()

        talks_filter = TalksFilter(request.GET, queryset=qs)
        serializer = TalkSerializer(talks_filter.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={201: TalkSerializer})
    def post(self, request):
        """Create a new talk."""
        serializer = TalkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TalkRetrieveUpdateDestroyView(APIView):
    """retrieve, update and destroy view for talks."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk, user):
        """Get talk by pk."""
        qs = Talks.objects.select_related(
            "speaker__user_account", "event"
        ).prefetch_related("talk_sessions")
        talk = get_object_or_404(qs, pk=pk)
        return talk

    @extend_schema(responses={200: TalkSerializer})
    def get(self, request, pk=None):
        """Retrieve a talk."""
        talk = self.get_object(pk, request.user)
        serializer = TalkSerializer(talk)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=TalkSerializer, responses={200: TalkSerializer})
    def patch(self, request, pk=None):
        """Update a talk."""
        talk = self.get_object(pk, request.user)
        if talk.speaker.user_account != request.user:
            raise PermissionDenied("You do not have permission to edit this talk.")
        serializer = TalkSerializer(talk, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, pk=None):
        """Delete a talk."""
        talk = self.get_object(pk, request.user)
        if talk.speaker.user_account != request.user:
            raise PermissionDenied("You do not have permission to delete this talk.")
        talk.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicTalkDetailView(APIView):
    """Public detail view for a specific talk."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: TalkSerializer})
    def get(self, request, slug=None):
        """Retrieve a public talk by slug."""
        talk = get_object_or_404(
            Talks.objects.filter(is_public=True)
            .select_related("speaker__user_account", "event")
            .prefetch_related("talk_sessions"),
            slug=slug,
        )
        serializer = TalkSerializer(talk)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpeakerPublicTalksView(APIView):
    """Public list view of talks for a specific speaker."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: TalkSerializer(many=True)})
    def get(self, request, slug=None):
        """List public talks for a speaker."""
        talks = (
            Talks.objects.filter(is_public=True, speaker__slug=slug)
            .select_related("speaker__user_account", "event")
            .prefetch_related("talk_sessions")
        )
        serializer = TalkSerializer(talks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TalkReviewSubmitView(APIView):
    """Public list and create view for talk reviews using a slug."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(responses={200: TalkReviewCommentSerializer(many=True)})
    def get(self, request, slug=None):
        """List reviews for a talk."""
        comments = TalkReviewComment.objects.filter(
            talk__slug=slug, talk__is_public=True
        ).select_related("talk")
        serializer = TalkReviewCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=TalkReviewCommentSerializer,
        responses={201: TalkReviewCommentSerializer},
    )
    def post(self, request, slug=None):
        """Submit a review for a talk."""
        try:
            talk = Talks.objects.get(slug=slug)
        except Talks.DoesNotExist as err:
            raise ValidationError({"talk": "Talk does not exist."}) from err

        if not talk.is_reviewable:
            raise PermissionDenied("This talk is no longer accepting reviews.")

        serializer = TalkReviewCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(talk=talk)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
