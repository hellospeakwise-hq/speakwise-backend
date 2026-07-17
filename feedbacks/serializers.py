"""Serializers for the feedback app."""

from rest_framework import serializers

from events.models import Event
from feedbacks.models import EventFeedbackPreference, Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with support for anonymous feedback."""

    # Required on submission even though the model column is nullable for
    # legacy rows — event-based feedback gating depends on it.
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]


class EventFeedbackPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for a speaker's per-event feedback preference."""

    is_feedback_enabled = serializers.BooleanField()

    class Meta:
        """Meta options."""

        model = EventFeedbackPreference
        fields = ["event", "is_feedback_enabled"]
        read_only_fields = ["event"]
