"""Feedback views."""

from django.core.signing import BadSignature
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from feedbacks.models import Feedback
from feedbacks.serializers import FeedbackSerializer
from feedbacks.services import (
    mark_attendance_feedback_given,
    verify_feedback_token,
)


class FeedbackThrottle(UserRateThrottle):
    """Throttle for feedback requests."""

    scope = "feedback"


class FeedbackPagination(PageNumberPagination):
    """Pagination for feedback lists."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class FeedbackListCreateView(APIView):
    """List and create feedback."""

    serializer_class = FeedbackSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(responses=FeedbackSerializer(many=True))
    def get(self, request, *args, **kwargs):
        """List feedbacks for the authenticated speaker."""
        feedbacks = Feedback.objects.filter(
            speaker__user_account=request.user
        ).select_related("speaker__user_account")
        feedbacks = feedbacks.order_by("-created_at")
        paginator = FeedbackPagination()
        page = paginator.paginate_queryset(feedbacks, request)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = self.serializer_class(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=FeedbackSerializer, responses=FeedbackSerializer)
    def post(self, request, *args, **kwargs):
        """Create a new feedback."""
        self.throttle_classes = [FeedbackThrottle]
        self.check_throttles(request)
        """Create a new feedback.

        Requires prior attendee verification via the verify endpoint.
        If not verified, returns 403 with a link to the verification endpoint.

        Verification is passed via a signed ``verify_token`` query parameter
        (set by the verify-attendee endpoint) so it works across distributed workers.
        """
        verify_token = request.query_params.get("verify_token") or request.data.get(
            "verify_token"
        )
        if not verify_token:
            verify_url = reverse("attendees:verify-attendee")
            return Response(
                {
                    "detail": "Attendee verification required before submitting feedback.",
                    "verify_url": f"/api/{verify_url.lstrip('/')}",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            email = verify_feedback_token(verify_token)
        except BadSignature:
            return Response(
                {"detail": "Invalid or expired verification token."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        mark_attendance_feedback_given(email)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
