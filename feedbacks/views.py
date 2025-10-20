"""Feedback views using Generic Views."""

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Feedback
from .serializers import FeedbackCreateSerializer, FeedbackSerializer


@extend_schema(
    request=FeedbackCreateSerializer,
    responses=FeedbackSerializer(many=True),
    tags=["Feedbacks"],
)
class FeedbackListCreateView(generics.ListCreateAPIView):
    """List and create feedback."""

    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve."""
        if self.request.method == "POST":
            return FeedbackCreateSerializer
        return FeedbackSerializer

    def get_queryset(self):
        """Optimize query with select_related for attendee."""
        return Feedback.objects.select_related("attendee").all()


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
        return Feedback.objects.select_related("attendee").all()


def verify_attendee(request):
    """verify attendee>"""
    at_email = request.get("email")
    try:
        return AttendeeProfile.objects.get(email=at_email)
    except AttendeeProfile.DoesNotExist:
        return False
