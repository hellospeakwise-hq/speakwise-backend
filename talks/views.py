"""talks views."""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from talks.filters import TalksFilter
from talks.models import Talks
from talks.permissions import CanReviewTalks
from talks.serializers import TalkReviewSerializer, TalkSerializer


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


@extend_schema(responses=TalkReviewSerializer)
class TalkReviewRetrieveView(RetrieveAPIView):
    """Retrieve view for reviewing talks - restricted to talk reviewers, organizers, and admins."""

    queryset = Talks.objects.select_related(
        "speaker", "speaker__user_account", "event"
    ).prefetch_related("talk_sessions")
    serializer_class = TalkReviewSerializer
    permission_classes = [CanReviewTalks]
