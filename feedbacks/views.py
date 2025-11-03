"""Feedback views using Generic Views."""

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackListCreateView(APIView):
    """List and create feedback."""

    serializer_class = FeedbackSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(responses=FeedbackSerializer(many=True))
    def get(self, request, *args, **kwargs):
        """List feedbacks for the authenticated speaker."""
        feedbacks = Feedback.objects.filter(speaker__user_account=request.user)
        serializer = self.serializer_class(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=FeedbackSerializer, responses=FeedbackSerializer)
    def post(self, request, *args, **kwargs):
        """Create a new feedback."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=FeedbackSerializer,
    responses=FeedbackSerializer,
    tags=["Feedbacks"],
)
class FeedbackRetrieveUpdateDestroyView(
    generics.RetrieveAPIView, generics.DestroyAPIView
):
    """Retrieve, update and destroy feedback."""

    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Optimize query with select_related for attendee."""
        return Feedback.objects.filter(speaker__user_account=self.request.user)
