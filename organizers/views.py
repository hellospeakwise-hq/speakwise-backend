"""Organizer views using Generic Views."""

from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendees.models import Attendance
from base.permissions import IsAdminOrOrganizer, IsOrganizer
from base.utils import FileHandler
from speakers.serializers import  SpeakerSocialLinksSerializer

from .serializers import AttendanceSerializer, OrganizerProfileSerializer


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


class FileUploadDetailView(APIView):
    """File upload detail view."""

    permission_classes = [AllowAny]

    def get_object(self, pk):
        """Get object by pk."""
        try:
            return Attendance.objects.get(pk=pk)
        except Attendance.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses={200: AttendanceSerializer})
    def patch(self, request, pk=None):
        """Update an email."""
        email = get_object_or_404(pk)
        serializer = AttendanceSerializer(email, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        """Delete an attendance email."""
        email = self.get_object(pk)
        email.delete()
        return Response(
            {"message": "Email deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class FileUploadViewCreatView(APIView):
    """File upload view."""

    file_handler = FileHandler()
    permission_classes = [IsAdminOrOrganizer]
    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def post(self, request, *args, **kwargs):
        """Process the uploaded file."""
        file_obj = request.FILES.get("file")
        event_id = request.data.get("event")
        print("EVENT ID: ", event_id)
        if not file_obj:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not event_id:
            return Response(
                {"error": "Event ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get the event object
        try:
            from events.models import Event

            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Process the file with your FileHandler
        try:
            self.file_handler.clean_file(file_obj, event)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        attendance_list = Attendance.objects.filter(event=event)
        serializer = AttendanceSerializer(attendance_list, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=AttendanceSerializer(many=True))
    def get(self, request):
        """Get all attendance emails."""
        emails = Attendance.objects.all()
        serializer = AttendanceSerializer(emails, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
