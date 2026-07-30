"""CFP views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import IsOrganizationAdminOrOrganizer
from cfps.choices import CFPStatusChoices
from cfps.models import CFPReview, CFPSubmission
from cfps.serializers import (
    CFPReviewDetailSerializer,
    CFPReviewSerializer,
    CFPStatusUpdateSerializer,
    CFPSubmissionSerializer,
    CFPSubmissionWithScoreSerializer,
)
from cfps.services import CFPEmailService
from events.models import Event


@extend_schema(tags=["CFP"])
class CFPSubmissionListCreateView(ListCreateAPIView):
    """GET  — organizers see all submissions for the event.
    POST — any authenticated user submits a CFP.
    """

    serializer_class = CFPSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_event(self):
        """Return the event for this request, cached on the view instance."""
        if not hasattr(self, "_event"):
            self._event = get_object_or_404(Event, slug=self.kwargs["slug"])
        return self._event

    def get_serializer_class(self):
        """Organizers get score/review data; submitters get the plain serializer."""
        event = self.get_event()
        if IsOrganizationAdminOrOrganizer().has_object_permission(
            self.request, self, event
        ):
            return CFPSubmissionWithScoreSerializer
        return CFPSubmissionSerializer

    def get_serializer_context(self):
        """Inject request into serializer context for score aggregation."""
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def get_queryset(self):
        """Return submissions scoped to the event and user role."""
        event = self.get_event()
        if IsOrganizationAdminOrOrganizer().has_object_permission(
            self.request, self, event
        ):
            return CFPSubmission.objects.filter(event=event).prefetch_related(
                "co_speakers", "reviews__reviewer"
            )
        return CFPSubmission.objects.filter(
            event=event, submitter=self.request.user
        ).prefetch_related("co_speakers")

    def perform_create(self, serializer):
        """Save the submission."""
        serializer.save(event=self.get_event(), submitter=self.request.user)


@extend_schema(tags=["CFP"])
class CFPSubmissionDetailView(RetrieveUpdateDestroyAPIView):
    """GET    — submitter or organizer.
    PATCH  — submitter only, while status is pending.
    DELETE — submitter only, while status is pending.
    """

    serializer_class = CFPSubmissionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Return all submissions with co_speakers prefetched."""
        return CFPSubmission.objects.prefetch_related("co_speakers")

    def get_object(self):
        """Return the submission if the user is the submitter or an organizer."""
        obj = super().get_object()
        user = self.request.user
        is_submitter = obj.submitter == user
        is_organizer = IsOrganizationAdminOrOrganizer().has_object_permission(
            self.request, self, obj
        )
        if not (is_submitter or is_organizer):
            raise PermissionDenied(
                "You do not have permission to access this submission."
            )
        return obj

    def perform_destroy(self, instance):
        """Delete the submission if it is still pending."""
        if instance.submitter != self.request.user:
            raise PermissionDenied("Only the submitter can delete this submission.")
        if instance.status != CFPStatusChoices.PENDING:
            raise PermissionDenied("Submissions can only be deleted while pending.")
        instance.delete()


@extend_schema(tags=["CFP"])
class MyCFPSubmissionsView(ListAPIView):
    """GET — returns all CFP submissions by the authenticated user across all events."""

    serializer_class = CFPSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return all submissions by the current user."""
        return (
            CFPSubmission.objects.filter(submitter=self.request.user)
            .prefetch_related("co_speakers")
            .select_related("event")
            .order_by("-event__start_date_time")
        )


@extend_schema(tags=["CFP"])
class CFPStatusUpdateView(UpdateAPIView):
    """PATCH — organizer updates submission status (accepted / rejected)."""

    serializer_class = CFPStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdminOrOrganizer]
    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):
        """Return all submissions."""
        return CFPSubmission.objects.all()

    def perform_update(self, serializer):
        """Save the status change and notify the submitter by email."""
        serializer.is_valid(raise_exception=True)
        serializer.save(submitter=self.request.user)
        submission = serializer.save()
        CFPEmailService.send_status_notification(submission)


@extend_schema(tags=["CFP"])
class CFPReviewQueueView(APIView):
    """GET — returns one random pending submission not yet reviewed by the current user.

    Response body:
        submission  — full CFP submission data with review aggregate fields
        progress    — { reviewed: int, total: int }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        """Return one random unreviewed pending submission for the current organizer."""
        event = get_object_or_404(Event, slug=slug)
        if not IsOrganizationAdminOrOrganizer().has_object_permission(
            request, self, event
        ):
            raise PermissionDenied("Only organizers can access the review queue.")

        pending_qs = CFPSubmission.objects.filter(
            event=event, status=CFPStatusChoices.PENDING
        ).prefetch_related("reviews", "co_speakers")
        total = pending_qs.count()

        reviewed_ids = CFPReview.objects.filter(
            reviewer=request.user,
            submission__event=event,
        ).values_list("submission_id", flat=True)
        reviewed_count = reviewed_ids.count()

        unreviewed = pending_qs.exclude(id__in=reviewed_ids)
        if not unreviewed.exists():
            return Response(
                {
                    "detail": "You have reviewed all pending submissions.",
                    "progress": {"reviewed": reviewed_count, "total": total},
                },
                status=status.HTTP_204_NO_CONTENT,
            )

        submission = unreviewed.order_by("?").first()
        serializer = CFPSubmissionWithScoreSerializer(
            submission, context={"request": request}
        )
        return Response(
            {
                "submission": serializer.data,
                "progress": {"reviewed": reviewed_count, "total": total},
            }
        )


@extend_schema(tags=["CFP"])
class CFPReviewView(APIView):
    """POST — submit or update a review score for a submission.

    Body: { score: 1-5, notes: "" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Submit or update a review score for a CFP submission."""
        submission = get_object_or_404(CFPSubmission, pk=pk)
        if not IsOrganizationAdminOrOrganizer().has_object_permission(
            request, self, submission
        ):
            raise PermissionDenied("Only organizers can review submissions.")

        serializer = CFPReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review, _ = CFPReview.objects.update_or_create(
            submission=submission,
            reviewer=request.user,
            defaults=serializer.validated_data,
        )
        return Response(CFPReviewSerializer(review).data, status=status.HTTP_200_OK)


@extend_schema(tags=["CFP"])
class CFPReviewListView(APIView):
    """GET — list all reviews for a submission (organizers only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """List all reviews for a submission."""
        submission = get_object_or_404(CFPSubmission, pk=pk)
        if not IsOrganizationAdminOrOrganizer().has_object_permission(
            request, self, submission
        ):
            raise PermissionDenied("Only organizers can view all reviews.")
        reviews = CFPReview.objects.filter(submission=submission).select_related(
            "reviewer"
        )
        return Response(CFPReviewDetailSerializer(reviews, many=True).data)
