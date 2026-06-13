"""attendees views."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendees.models import Attendance, AttendeeProfile
from attendees.serializers import (
    AttendanceSerializer,
    AttendeeProfileSerializer,
    FileUploadSerializer,
    VerifyAttendeeSerializer,
)
from attendees.services import verify_attendee_email
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
class VerifyAttendeeView(APIView):
    """Verify attendee before feedback.

    Validates the incoming email and checks if there's an attendance record.
    If found and feedback hasn't been given yet, mark the session as verified so
    the attendee can proceed to submit feedback.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyAttendeeSerializer, responses={200: VerifyAttendeeSerializer}
    )
    def post(self, request):
        """Verify attendee by email."""
        serializer = VerifyAttendeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            result = verify_attendee_email(email)
        except Attendance.DoesNotExist:
            return Response(
                {"detail": "Attendee not found", "email": email},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as err:
            return Response(
                {"detail": str(err), "email": email},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class AttendancePagination(PageNumberPagination):
    """Pagination for attendance lists."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class CreateAttendanceByFileUploadView(APIView):
    """Attendee list create view."""

    permission_classes = [IsOrganizationAdmin]
    pagination_class = AttendancePagination

    def get(self, request):
        """Return attendance objects with optional event filtering and pagination."""
        qs = Attendance.objects.select_related("event").all()
        event_id = request.query_params.get("event")
        if event_id:
            qs = qs.filter(event_id=event_id)
        qs = qs.order_by("-check_in_time")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = AttendanceSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = AttendanceSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=AttendanceSerializer, responses=AttendanceSerializer)
    def post(self, request):
        """Create attendance by file upload."""
        serializer = AttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AttendanceDetailView(APIView):
    """get attendance detail view."""

    permission_classes = [IsOrganizationOrganizer]

    def get_object(self, pk):
        """Get attendance object."""
        try:
            return Attendance.objects.get(pk=pk)
        except Attendance.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=AttendanceSerializer)
    def get(self, request, pk):
        """Get attendance detail."""
        attendance = self.get_object(pk)
        serializer = AttendanceSerializer(attendance)
        return Response(serializer.data)

    @extend_schema(request=AttendanceSerializer)
    def patch(self, request, pk):
        """Update attendance detail."""
        attendance = self.get_object(pk)
        serializer = AttendanceSerializer(attendance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        """Delete attendance detail."""
        attendance = self.get_object(pk)
        attendance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=FileUploadSerializer, responses=AttendanceSerializer(many=True))
class UploadAttendanceView(APIView):
    """Create attendance objects from uploaded file."""

    permission_classes = [IsOrganizationAdmin]

    @extend_schema(
        request=FileUploadSerializer, responses=AttendanceSerializer(many=True)
    )
    def post(self, request):
        """Upload attendance file and create attendance records."""
        attendance_file = request.FILES.get("file")
        event_id = request.data.get("event")

        if not attendance_file:
            return Response(
                {
                    "detail": "No file uploaded. Use multipart/form-data with field 'file'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not event_id:
            return Response(
                {"detail": "'event' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
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
