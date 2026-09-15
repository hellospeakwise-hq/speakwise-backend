"""Feedback views using Generic Views."""

from io import BytesIO

import qrcode
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, Throttled
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from feedbacks.models import Feedback
from feedbacks.serializers import (
    FeedbackRateSerializer,
    FeedbackReadSerializer,
    FeedbackSubmittedSerializer,
)
from feedbacks.services import (
    build_feedback_qr_payload,
    hash_submitter_ip,
    is_feedback_open,
    resolve_feedback_experience,
    submitted_recently_by_ip,
)
from users.permissions import IsEmailVerified


class FeedbackListView(APIView):
    """List the authenticated speaker's own feedback."""

    permission_classes = [IsAuthenticated]
    serializer_class = FeedbackReadSerializer

    @extend_schema(responses=FeedbackReadSerializer(many=True))
    def get(self, request, *args, **kwargs):
        """List feedback for the authenticated speaker, optionally per-experience."""
        queryset = Feedback.objects.filter(speaker__user_account=request.user)
        feedback_slug = request.query_params.get("experience")
        if feedback_slug:
            experience = resolve_feedback_experience(feedback_slug)
            if experience is None:
                raise NotFound("Unknown experience.")
            queryset = queryset.filter(experience=experience)

        serializer = self.serializer_class(
            queryset.select_related("experience"), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class FeedbackRateView(APIView):
    """Public endpoint to rate a specific presentation via its QR slug.

    No authentication is required. The experience slug, resolved from the URL,
    identifies both the speaker and the presentation.
    """

    permission_classes = [AllowAny]
    serializer_class = FeedbackRateSerializer

    @extend_schema(
        request=FeedbackRateSerializer, responses=FeedbackSubmittedSerializer
    )
    def post(self, request, feedback_slug, *args, **kwargs):
        """Submit anonymous or named feedback for a presentation."""
        experience = resolve_feedback_experience(feedback_slug)
        if experience is None:
            raise NotFound("Presentation not found.")

        if not is_feedback_open(experience):
            raise PermissionDenied("Feedback for this presentation has not opened yet.")
        if not experience.feedback_enabled:
            raise PermissionDenied(
                "The speaker is not accepting feedback for this presentation."
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = self._client_ip(request)
        ip_hash = hash_submitter_ip(ip) if ip else ""
        if ip_hash and submitted_recently_by_ip(experience, ip_hash):
            raise Throttled(
                detail="You have already submitted feedback for this presentation."
            )

        feedback = serializer.save(
            experience=experience,
            speaker=experience.speaker,
            submitter_ip_hash=ip_hash,
        )
        return Response(
            FeedbackSubmittedSerializer(feedback).data, status=status.HTTP_201_CREATED
        )

    @staticmethod
    def _client_ip(request) -> str:
        """Return the request's originating IP address, or an empty string."""
        return request.META.get("REMOTE_ADDR", "")


class FeedbackQRCodeView(APIView):
    """Return a PNG QR code for the audience to rate a presentation."""

    permission_classes = [IsEmailVerified]

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, feedback_slug, *args, **kwargs):
        """Generate a QR code encoding the public rating URL."""
        experience = resolve_feedback_experience(feedback_slug)
        if experience is None:
            raise NotFound("Presentation not found.")
        if experience.speaker.user_account != request.user:
            raise PermissionDenied("You do not own this presentation.")

        payload = build_feedback_qr_payload(feedback_slug)
        image = qrcode.make(payload)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return HttpResponse(buffer.getvalue(), content_type="image/png")
