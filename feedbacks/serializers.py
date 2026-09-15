"""Serializers for the feedback app."""

from rest_framework import serializers

from feedbacks.models import RATING_FIELDS, Feedback
from profiles.models.speaker_models import SpeakerExperiences


class FeedbackRateSerializer(serializers.ModelSerializer):
    """Public submission serializer for rating a presentation.

    The audience only supplies optional name, optional comments, and the six
    ratings. The experience (and thus the speaker) is resolved from the URL
    slug, so no internal identifiers are accepted from the client.
    """

    name = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )

    class Meta:
        """Meta options."""

        model = Feedback
        fields = ["name", "comments", *RATING_FIELDS]


class FeedbackExperienceSummarySerializer(serializers.ModelSerializer):
    """Minimal read representation of the experience a feedback row belongs to."""

    class Meta:
        """Meta options."""

        model = SpeakerExperiences
        fields = ["feedback_slug", "event_name", "event_date", "topic"]


class FeedbackReadSerializer(serializers.ModelSerializer):
    """Read shape for feedback returned to the speaker's own list."""

    experience = FeedbackExperienceSummarySerializer(read_only=True)

    class Meta:
        """Meta options."""

        model = Feedback
        fields = [
            "id",
            "experience",
            "speaker",
            "name",
            "is_anonymous",
            *RATING_FIELDS,
            "comments",
            "created_at",
        ]
        read_only_fields = ["speaker"]


class FeedbackSubmittedSerializer(serializers.ModelSerializer):
    """Audience-facing response after a successful submission.

    Deliberately excludes internal model identifiers so no UUIDs leak to the
    page that scanned the QR code.
    """

    experience = FeedbackExperienceSummarySerializer(read_only=True)

    class Meta:
        """Meta options."""

        model = Feedback
        fields = [
            "experience",
            "name",
            "is_anonymous",
            *RATING_FIELDS,
            "comments",
            "created_at",
        ]
