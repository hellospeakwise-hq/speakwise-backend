"""Feedback views using Generic Views."""

from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendees.models import Attendance

from .models import Feedback
from .serializers import FeedbackSerializer


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
        feedbacks = Feedback.objects.filter(speaker__user_account=request.user)
        serializer = self.serializer_class(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=FeedbackSerializer, responses=FeedbackSerializer)
    def post(self, request, *args, **kwargs):
        """Create a new feedback.

        Requires prior attendee verification via the verify endpoint.
        If not verified, returns 403 with a link to the verification endpoint.
        """
        if not request.session.get("attendee_verified"):
            verify_url = reverse("attendees:verify-attendee")
            # Namespace is mounted under /api/ at project level
            return Response(
                {
                    "detail": "Attendee verification required before submitting feedback.",
                    "verify_url": f"/api/{verify_url.lstrip('/')}",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Mark attendance as having given feedback based on verified email.
        email = request.session.get("attendee_email")
        if email:
            Attendance.objects.filter(email=email, is_given_feedback=False).update(
                is_given_feedback=True
            )

        # Clear verification flags after successful submission.
        request.session["attendee_verified"] = False
        request.session.pop("attendee_email", None)
        request.session.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
