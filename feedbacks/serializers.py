"""Serializers for the feedback app."""

from rest_framework import serializers

from feedbacks.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with support for anonymous feedback."""

    sessionType = serializers.CharField(
        source="session.type", read_only=True, allow_null=True
    )

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]
