"""attendees views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from attendees.models import Attendance, AttendeeProfile
from attendees.serializers import (
    AttendanceSerializer,
    AttendeeProfileSerializer,
    FileUploadSerializer,
    VerifyAttendeeSerializer,
)
from base.permissions import IsOrganizationAdmin, IsOrganizationOrganizer
from base.utils import FileHandler
from events.models import Event


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


class CreateAttendanceByFileUploadView(ListCreateAPIView):
    """Attendee list create view."""

    permission_classes = [IsOrganizationAdmin]
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class AttendanceDetailView(RetrieveUpdateDestroyAPIView):
    """get attendance detail view."""

    permission_classes = [IsOrganizationOrganizer]
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


@api_view(["POST"])
@extend_schema(request=FileUploadSerializer, responses=AttendanceSerializer(many=True))
def upload_attendance_view(request, *args, **kwargs):
    """Create attendance objects from uploaded file."""
    attendance_file = request.FILES.get("file")
    event = Event.objects.get(id=int(request.data.get("event")))

    if not attendance_file:
        return Response(
            {"detail": "No file uploaded. Use multipart/form-data with field 'file'."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not event:
        return Response(
            {"detail": "'event' is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        attendance = FileHandler().clean_file(file_obj=attendance_file, event=event)
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"detail": "Unable to process file.", "error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = AttendanceSerializer(attendance, many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
