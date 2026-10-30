"""Serializers for the feedback app."""

from rest_framework import serializers

from feedbacks.models import RATING_FIELDS, Feedback
from profiles.models.speaker_models import SpeakerExperiences


class FeedbackExperienceInfoSerializer(serializers.ModelSerializer):
    """Public-safe experience info returned by GET /feedbacks/rate/<slug>/.

    Exposes presentation context so the audience landing page can display the
    talk title, event, and speaker name without leaking any internal IDs.
    Also exposes ``is_open`` so the page can detect a closed/gated form
    before the user even attempts to submit.
    """

    speaker_name = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

    class Meta:
        """Meta options."""

        model = SpeakerExperiences
        fields = [
            "topic",
            "event_name",
            "event_date",
            "speaker_name",
            "feedback_enabled",
            "is_open",
        ]

    def get_speaker_name(self, obj) -> str:
        """Return the speaker's full name from their user account."""
        user = getattr(getattr(obj, "speaker", None), "user_account", None)
        if user is None:
            return ""
        first = user.first_name or ""
        last = user.last_name or ""
        return f"{first} {last}".strip() or user.username

    def get_is_open(self, obj) -> bool:
        """Return whether the date gate allows feedback submission right now."""
        from feedbacks.services import is_feedback_open

        return is_feedback_open(obj)


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


class SpeakBotQuerySerializer(serializers.Serializer):
    """Input query for SpeakBot AI Coach."""

    query = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=2000,
        help_text="Speaker query or question for the AI coach.",
    )
    experience = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        help_text="Optional UUID or feedback_slug to scope coaching to a single talk.",
    )
    history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="Optional list of previous messages [{'role': 'user'|'assistant', 'content': '...'}]",
    )


class SpeakBotSummarySerializer(serializers.Serializer):
    """Summary metrics included in SpeakBot response."""

    total_feedbacks = serializers.IntegerField()
    talks_analyzed = serializers.IntegerField()
    avg_rating = serializers.FloatField(allow_null=True)
    top_strength = serializers.CharField(allow_null=True)
    top_growth_area = serializers.CharField(allow_null=True)


class SpeakBotResponseSerializer(serializers.Serializer):
    """Response returned by SpeakBot AI Coach."""

    reply = serializers.CharField(help_text="Markdown formatted coaching advice.")
    provider = serializers.CharField(
        help_text="AI provider used (gemini, groq, analytics_fallback)."
    )
    model = serializers.CharField(
        allow_null=True, help_text="Specific model used for generation."
    )
    summary = SpeakBotSummarySerializer()
