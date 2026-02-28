"""talks views."""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from talks.filters import TalksFilter
from talks.models import TalkReviewComment, Talks
from talks.serializers import TalkReviewCommentSerializer, TalkSerializer


@extend_schema(request=TalkSerializer, responses=TalkSerializer)
class TalkListCreateView(ListCreateAPIView):
    """list and create view for talks."""

    queryset = Talks.objects.all()
    serializer_class = TalkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TalksFilter


class TalkRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """retrieve, update and destroy view for talks."""

    queryset = Talks.objects.all()
    serializer_class = TalkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class PublicTalkDetailView(RetrieveAPIView):
    """Public detail view for a specific talk."""

    queryset = Talks.objects.filter(is_public=True)
    serializer_class = TalkSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"


class SpeakerPublicTalksView(ListAPIView):
    """Public list view of talks for a specific speaker."""

    serializer_class = TalkSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter talks by public visibility and speaker slug."""
        speaker_slug = self.kwargs.get("slug")
        return Talks.objects.filter(is_public=True, speaker__slug=speaker_slug)


class TalkReviewSubmitView(ListCreateAPIView):
    """Public list and create view for talk reviews using a slug."""

    serializer_class = TalkReviewCommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter comments by the parent talk slug from the URL."""
        slug = self.kwargs.get("slug")
        return TalkReviewComment.objects.filter(talk__slug=slug)

    def perform_create(self, serializer):
        """Set the talk on creation and validate it is reviewable."""
        slug = self.kwargs.get("slug")

        try:
            talk = Talks.objects.get(slug=slug)
        except Talks.DoesNotExist as err:
            raise ValidationError({"talk": "Talk does not exist."}) from err

        if not talk.is_reviewable:
            raise PermissionDenied("This talk is no longer accepting reviews.")

        serializer.save(talk=talk)
