"""Serializers for the feedback app."""

from rest_framework import serializers

from feedbacks.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with support for anonymous feedback."""

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]
