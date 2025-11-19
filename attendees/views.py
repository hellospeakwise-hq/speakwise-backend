"""attendees views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from attendees.models import AttendeeProfile
from attendees.serializers import AttendeeProfileSerializer


@extend_schema(responses=AttendeeProfileSerializer, request=AttendeeProfileSerializer)
class AttendeeListCreateView(ListCreateAPIView):
    """attendee list create view."""

    serializer_class = AttendeeProfileSerializer
    permission_classes = [AllowAny]
    queryset = AttendeeProfile.objects.all()


@extend_schema(responses=AttendeeProfileSerializer, request=AttendeeProfileSerializer)
class AttendeeRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """attendee retrieve update and delete view."""

    serializer_class = AttendeeProfileSerializer
    queryset = AttendeeProfile.objects.all()
    permission_classes = [IsAuthenticated]

