"""CFP views."""

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from cfp.choices import CFPStatusChoices
from cfp.models import CFPSubmission
from cfp.serializers import CFPStatusUpdateSerializer, CFPSubmissionSerializer
from cfp.services import CFPEmailService
from events.models import Event
from organizations.models import OrganizationMembership


def _get_event_or_404(slug):
    try:
        return Event.objects.get(slug=slug)
    except Event.DoesNotExist as err:
        raise NotFound("Event not found.") from err


def _is_event_organizer(user, event):
    return OrganizationMembership.objects.filter(
        organization=event.organizer,
        user=user,
        role__in=["ADMIN", "ORGANIZER"],
    ).exists()


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
            self._event = _get_event_or_404(self.kwargs["slug"])
        return self._event

    def get_queryset(self):
        """Return submissions scoped to the event and user role."""
        event = self.get_event()
        user = self.request.user
        if _is_event_organizer(user, event):
            return CFPSubmission.objects.filter(event=event).prefetch_related(
                "co_speakers"
            )
        return CFPSubmission.objects.filter(
            event=event, submitter=user
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
        is_organizer = _is_event_organizer(user, obj.event)
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
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):
        """Return all submissions."""
        return CFPSubmission.objects.all()

    def get_object(self):
        """Return the submission if the user is an event organizer."""
        obj = super().get_object()
        if not _is_event_organizer(self.request.user, obj.event):
            raise PermissionDenied(
                "Only event organizers can update submission status."
            )
        return obj

    def perform_update(self, serializer):
        """Save the status change and notify the submitter by email."""
        submission = serializer.save()
        CFPEmailService.send_status_notification(submission)
