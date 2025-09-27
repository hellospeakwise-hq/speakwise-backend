"""Serializers for the feedback app."""

from rest_framework import serializers

from feedbacks.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with support for anonymous feedback."""

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]

    def to_representation(self, instance):
        """Override to handle anonymous feedback display."""
        representation = super().to_representation(instance)

        # If feedback is anonymous, hide attendee information
        if instance.is_anonymous:
            representation["attendee"] = None

        return representation


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating feedback."""

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]

    def validate(self, data):
        """Validate rating fields are within acceptable range."""
        rating_fields = [
            "overall_rating",
            "engagement",
            "clarity",
            "content_depth",
            "speaker_knowledge",
            "practical_relevance",
        ]

        for field in rating_fields:
            if field in data and (data[field] < 1 or data[field] > 10):
                raise serializers.ValidationError(f"{field} must be between 1 and 10")
        return data

    def validate_attendee(self, value):
        """Ensure attendee can only submit one feedback per session."""
        session = self.initial_data.get("session")
        if Feedback.objects.filter(attendee=value, session=session).exists():
            raise serializers.ValidationError(
                "Attendee has already submitted feedback for this session."
            )
        return value
