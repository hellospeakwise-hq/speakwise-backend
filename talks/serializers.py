"""talks serializers."""

from rest_framework import serializers

from events.models import Event
from talks.models import TalkReviewComment, Talks, TalkSession


class SessionSerializer(serializers.ModelSerializer):
    """Session serializer."""

    class Meta:
        """Meta options."""

        model = TalkSession
        exclude = ("created_at", "updated_at", "talk")


class TalkSerializer(serializers.ModelSerializer):
    """Serializer for Talk model."""

    speaker_name = serializers.SerializerMethodField()
    session = SessionSerializer(required=False, many=False)
    event_title = serializers.SerializerMethodField()
    event_image = serializers.SerializerMethodField()
    event_location = serializers.SerializerMethodField()

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

    def get_event_title(self, obj) -> str:
        """Get the title of the event."""
        return obj.event.title if obj.event else ""

    def get_event_image(self, obj) -> str:
        """Get the image URL of the event."""
        if obj.event and obj.event.event_image:
            try:
                request = self.context.get("request")
                if request is not None:
                    return request.build_absolute_uri(obj.event.event_image.url)
                return obj.event.event_image.url
            except Exception:
                return obj.event.event_image.url
        return ""

    def get_event_location(self, obj) -> str:
        """Get the location of the event."""
        return obj.event.location if obj.event else ""

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
        from profiles.models import SpeakerProfile

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
