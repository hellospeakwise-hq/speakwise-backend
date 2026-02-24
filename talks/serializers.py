"""talks serializers."""

from rest_framework import serializers

from talks.models import Session, Talks


class SessionSerializer(serializers.ModelSerializer):
    """Session serializer."""

    class Meta:
        """Meta options."""

        model = Session
        exclude = ("created_at", "updated_at", "talk")


class TalkSerializer(serializers.ModelSerializer):
    """Serializer for Talk model."""

    speaker_name = serializers.SerializerMethodField()

    session = SessionSerializer(required=False, many=False)

    class Meta:
        """meta options."""

        model = Talks
        exclude = ("created_at", "updated_at")
        read_only_fields = ("slug",)

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        return (
            obj.speaker.user_account.first_name
            + " "
            + obj.speaker.user_account.last_name
        )


class TalkReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviewing talk proposals.

    Only returns public talks (is_public=True).
    """

    speaker_name = serializers.SerializerMethodField()
    speaker_email = serializers.SerializerMethodField()

    class Meta:
        """Meta options."""

        model = Talks
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "duration",
            "category",
            "presentation_files",
            "event",
            "is_public",
            "speaker_name",
            "speaker_email",
            "created_at",
        ]
        read_only_fields = fields

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        return (
            obj.speaker.user_account.first_name
            + " "
            + obj.speaker.user_account.last_name
        )

    def get_speaker_email(self, obj) -> str:
        """Get speaker email."""
        return obj.speaker.user_account.email
