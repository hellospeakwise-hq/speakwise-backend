"""Serializers for the feedback app."""

from rest_framework import serializers

from feedbacks.models import Feedback, SpeakerFeedbackSettings


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with support for anonymous feedback."""

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]


class SpeakerFeedbackSettingsSerializer(serializers.ModelSerializer):
    """Serializer for the per-event speaker feedback toggle."""

    class Meta:
        """Meta options."""

        model = SpeakerFeedbackSettings
        fields = ["id", "speaker", "event", "feedback_enabled"]
        read_only_fields = ["id", "speaker", "feedback_enabled"]
