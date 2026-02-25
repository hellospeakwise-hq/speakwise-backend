"""talks views."""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
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


class TalkReviewCommentListCreateView(ListCreateAPIView):
    """list and create view for talk review comments."""

    queryset = TalkReviewComment.objects.all()
    serializer_class = TalkReviewCommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter comments by the parent talk id from the URL, if provided."""
        qs = super().get_queryset()
        talk_id = self.kwargs.get("talk_id")
        if talk_id is not None:
            qs = qs.filter(talk_id=talk_id)
        return qs

    def perform_create(self, serializer):
        """Set the talk on creation using the URL kwarg rather than requiring it in payload."""
        talk_id = self.kwargs.get("talk_id")
        if talk_id is not None:
            serializer.save(talk_id=talk_id)
        else:
            # fall back to default behaviour; should rarely happen because the
            # URL pattern always provides a talk_id
            serializer.save()
