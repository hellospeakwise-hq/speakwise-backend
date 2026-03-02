"""talks serializers."""

from rest_framework import serializers

from talks.models import Session, TalkReviewComment, Talks


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
        read_only_fields = ["slug", "speaker_name"]

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        return (
            obj.speaker.user_account.first_name
            + " "
            + obj.speaker.user_account.last_name
        )


class TalkReviewCommentSerializer(serializers.ModelSerializer):
    """Talk review comment serializer."""

    class Meta:
        """Meta options."""

        model = TalkReviewComment
        exclude = ("created_at", "updated_at")
