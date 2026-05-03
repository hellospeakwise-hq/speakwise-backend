"""CFP views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from cfps.choices import CFPStatusChoices
from cfps.models import CFPSubmission
from cfps.permissions import IsEventOrganizer
from cfps.serializers import CFPStatusUpdateSerializer, CFPSubmissionSerializer
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

    def get_queryset(self):
        """Return submissions scoped to the event and user role."""
        event = self.get_event()
        if IsEventOrganizer().has_object_permission(self.request, self, event):
            return CFPSubmission.objects.filter(event=event).prefetch_related(
                "co_speakers"
            )
        return CFPSubmission.objects.filter(
            event=event, submitter=self.request.user
        ).prefetch_related("co_speakers")

    def perform_create(self, serializer):
        """Validate uniqueness and save the submission."""
        event = self.get_event()
        user = self.request.user
        if CFPSubmission.objects.filter(event=event, submitter=user).exists():
            raise ValidationError("You have already submitted a CFP for this event.")
        serializer.save(event=event, submitter=user)


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
        is_organizer = IsEventOrganizer().has_object_permission(self.request, self, obj)
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
class CFPStatusUpdateView(UpdateAPIView):
    """PATCH — organizer updates submission status (accepted / rejected)."""

    serializer_class = CFPStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsEventOrganizer]
    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):
        """Return all submissions."""
        return CFPSubmission.objects.all()

    def perform_update(self, serializer):
        """Save the status change and notify the submitter by email."""
        submission = serializer.save()
        CFPEmailService.send_status_notification(submission)
