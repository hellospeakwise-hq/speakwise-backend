"""CFP views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer
from cfps.choices import CFPStatusChoices
from cfps.models import CFPSubmission
from cfps.serializers import CFPStatusUpdateSerializer, CFPSubmissionSerializer
from cfps.services import CFPEmailService
from events.models import Event


@extend_schema(tags=["CFP"])
class CFPSubmissionListCreateView(APIView):
    """GET  — organizers see all submissions for the event.
    POST — any authenticated user submits a CFP.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: CFPSubmissionSerializer(many=True)},
    )
    def get(self, request, slug=None):
        """List submissions scoped to the event and user role."""
        event = get_object_or_404(Event, slug=slug)
        base_qs = CFPSubmission.objects.filter(event=event).prefetch_related(
            "co_speakers"
        )

        if IsOrganizationAdminOrOrganizer().has_object_permission(request, self, event):
            serializer = CFPSubmissionSerializer(base_qs, many=True)
        else:
            submissions = base_qs.filter(submitter=request.user)
            serializer = CFPSubmissionSerializer(submissions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=CFPSubmissionSerializer,
        responses={201: CFPSubmissionSerializer},
    )
    def post(self, request, slug=None):
        """Create a new CFP submission."""
        event = get_object_or_404(Event, slug=slug)
        serializer = CFPSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event, submitter=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["CFP"])
class CFPSubmissionDetailView(APIView):
    """GET    — submitter or organizer.
    PATCH  — submitter only, while status is pending.
    DELETE — submitter only, while status is pending.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """Return the submission if the user is the submitter or an organizer."""
        obj = get_object_or_404(
            CFPSubmission.objects.select_related("submitter", "event").prefetch_related(
                "co_speakers"
            ),
            pk=pk,
        )
        is_submitter = obj.submitter == user
        is_organizer = IsOrganizationAdminOrOrganizer().has_object_permission(
            self.request, self, obj
        )
        if not (is_submitter or is_organizer):
            raise PermissionDenied(
                "You do not have permission to access this submission."
            )
        return obj

    @extend_schema(responses={200: CFPSubmissionSerializer})
    def get(self, request, pk=None):
        """Retrieve a specific CFP submission."""
        submission = self.get_object(pk, request.user)
        serializer = CFPSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=CFPSubmissionSerializer, responses={200: CFPSubmissionSerializer}
    )
    def patch(self, request, pk=None):
        """Update a CFP submission (submitter only, pending status only)."""
        submission = self.get_object(pk, request.user)
        if submission.submitter != request.user:
            raise PermissionDenied("Only the submitter can edit this submission.")

        serializer = CFPSubmissionSerializer(
            submission, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses={204: None})
    def delete(self, request, pk=None):
        """Delete a CFP submission (submitter only, pending status only)."""
        submission = self.get_object(pk, request.user)
        if submission.submitter != request.user:
            raise PermissionDenied("Only the submitter can delete this submission.")
        if submission.status != CFPStatusChoices.PENDING:
            raise PermissionDenied("Submissions can only be deleted while pending.")
        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["CFP"])
class MyCFPSubmissionsView(APIView):
    """GET — returns all CFP submissions by the authenticated user across all events."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CFPSubmissionSerializer(many=True)})
    def get(self, request):
        """Return all CFP submissions by the current user."""
        submissions = (
            CFPSubmission.objects.filter(submitter=request.user)
            .prefetch_related("co_speakers")
            .select_related("event")
            .order_by("-event__start_date_time")
        )
        serializer = CFPSubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["CFP"])
class CFPStatusUpdateView(APIView):
    """PATCH — organizer updates submission status (accepted / rejected)."""

    permission_classes = [IsAuthenticated, IsOrganizationAdminOrOrganizer]

    @extend_schema(
        request=CFPStatusUpdateSerializer,
        responses={200: CFPStatusUpdateSerializer},
    )
    def patch(self, request, pk=None):
        """Update submission status and notify the submitter."""
        submission = get_object_or_404(CFPSubmission, pk=pk)
        self.check_object_permissions(request, submission)

        serializer = CFPStatusUpdateSerializer(
            submission, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated_submission = serializer.save()
        CFPEmailService.send_status_notification(updated_submission)

        return Response(serializer.data, status=status.HTTP_200_OK)
