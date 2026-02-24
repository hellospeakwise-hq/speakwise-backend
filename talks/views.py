"""talks views."""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    DestroyAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from base.permissions import CanReviewTalks
from talks.filters import TalksFilter
from talks.models import Talks
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


@extend_schema(request=TalkReviewSerializer, responses=TalkReviewSerializer)
class TalkReviewListView(ListCreateAPIView):
    """List view for talk reviews.

    Returns only public talks (is_public=True) that the user can review.
    """

    serializer_class = TalkReviewSerializer
    permission_classes = [CanReviewTalks]

    def get_queryset(self):
        """Return only public talks."""
        return Talks.objects.filter(is_public=True)


class TalkReviewDetailView(RetrieveUpdateAPIView):
    """Detail view for a specific talk review.

    Returns a single public talk that the user can review.
    """

    serializer_class = TalkReviewSerializer
    permission_classes = [CanReviewTalks]
    lookup_field = "slug"

    def get_queryset(self):
        """Return only public talks."""
        return Talks.objects.filter(is_public=True)


class TalkReviewDeleteView(DestroyAPIView):
    """Delete view for a specific talk review.

    Only the speaker who created the talk can delete it.
    """

    serializer_class = TalkReviewSerializer
    permission_classes = [CanReviewTalks]
    lookup_field = "slug"
    queryset = Talks.objects.filter(is_public=True)

    def destroy(self, request, *args, **kwargs):
        """Check ownership before deleting."""
        if not request.user.is_authenticated:
            from rest_framework.response import Response
            from rest_framework import status

            return Response(
                {"detail": "Authentication required to delete a talk."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        instance = self.get_object()
        if instance.speaker.user_account != request.user:
            from rest_framework.response import Response
            from rest_framework import status

            return Response(
                {"detail": "You do not have permission to delete this talk."},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.perform_destroy(instance)
        from rest_framework.response import Response
        from rest_framework import status

        return Response(status=status.HTTP_204_NO_CONTENT)
