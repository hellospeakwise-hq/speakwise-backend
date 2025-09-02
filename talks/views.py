"""talks views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from talks.models import Talks
from talks.serializers import TalkSerializer


@extend_schema(request=TalkSerializer, responses=TalkSerializer)
class TalkListCreateView(ListCreateAPIView):
    """list and create view for talks."""

    queryset = Talks.objects.all()
    serializer_class = TalkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TalkRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """retrieve, update and destroy view for talks."""

    queryset = Talks.objects.all()
    serializer_class = TalkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
