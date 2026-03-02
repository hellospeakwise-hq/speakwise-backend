"""talks serializers."""

from rest_framework import serializers

from events.models import Event
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

    # event is optional for standalone / pre-CFP talks
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        """meta options."""

        model = Talks
        exclude = ("created_at", "updated_at")
        read_only_fields = ["slug", "speaker_name", "speaker"]

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        if not obj.speaker:
            return ""
        return (
            obj.speaker.user_account.first_name
            + " "
            + obj.speaker.user_account.last_name
        )

    def create(self, validated_data):
        """Auto-assign the speaker from the authenticated user."""
        from speakers.models import SpeakerProfile

        request = self.context.get("request")
        if request and request.user.is_authenticated:
            speaker = SpeakerProfile.objects.filter(user_account=request.user).first()
            if not speaker:
                raise serializers.ValidationError(
                    {"speaker": "No speaker profile found for this user."}
                )
            validated_data["speaker"] = speaker
        return super().create(validated_data)


class TalkReviewCommentSerializer(serializers.ModelSerializer):
    """Talk review comment serializer."""

    class Meta:
        """Meta options."""

        model = TalkReviewComment
        exclude = ("created_at", "updated_at")
