"""Organizer views using Generic Views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import OrganizerProfileSerializer

from drf_spectacular.utils import extend_schema


@extend_schema(
    request=OrganizerProfileSerializer,
    responses=OrganizerProfileSerializer(many=True),
    tags=["Organizers"],
)
class OrganizerProfileListCreateView(generics.ListCreateAPIView):
    """List and create organizer profiles."""

    serializer_class = OrganizerProfileSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    request=OrganizerProfileSerializer,
    responses=OrganizerProfileSerializer,
    tags=["Organizers"],
)
class OrganizerProfileRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and destroy organizer profiles."""

    serializer_class = OrganizerProfileSerializer
    permission_classes = [IsAuthenticated]
