"""attendees views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from attendees.models import Attendance, AttendeeProfile
from attendees.serializers import AttendeeProfileSerializer, VerifyAttendeeSerializer


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


@extend_schema(
    request=VerifyAttendeeSerializer, responses={200: VerifyAttendeeSerializer}
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_attendee(request):
    """Verify attendee before feedback.

    Validates the incoming email and checks if there's an attendance record.
    If found and feedback hasn't been given yet, mark the session as verified so
    the attendee can proceed to submit feedback.
    """
    serializer = VerifyAttendeeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]

    attendances = Attendance.objects.filter(email=email)
    if not attendances.exists():
        return Response(
            {"detail": "Attendee not found", "email": email},
            status=status.HTTP_404_NOT_FOUND,
        )

    if attendances.filter(is_given_feedback=True).exists():
        return Response(
            {"detail": "Attendee already given feedback", "email": email},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Mark session as verified to allow feedback submission.
    request.session["attendee_verified"] = True
    request.session["attendee_email"] = email
    request.session.save()

    return Response(
        {"detail": "Attendee verified. You may now submit feedback.", "email": email},
        status=status.HTTP_200_OK,
    )
