"""attendees views."""

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from attendees.models import Attendee
from attendees.serializers import AttendeeSerializer


@extend_schema(responses=AttendeeSerializer, request=AttendeeSerializer)
class AttendeeListCreateView(ListCreateAPIView):
    """attendee list create view."""

    serializer_class = AttendeeSerializer
    permission_classes = [AllowAny]
    queryset = Attendee.objects.all()


@extend_schema(responses=AttendeeSerializer, request=AttendeeSerializer)
class AttendeeRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """attendee retrieve update and delete view."""

    serializer_class = AttendeeSerializer
    queryset = Attendee.objects.all()
