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

    def get_speaker_name(self, obj):
        """Get speaker name."""
        return (
            obj.speaker.user_account.first_name
            + " "
            + obj.speaker.user_account.last_name
        )
