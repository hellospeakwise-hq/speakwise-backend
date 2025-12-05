"""speaker serializers."""

from drf_writable_nested.serializers import WritableNestedModelSerializer
from jsonschema import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from speakers.models import (
    SpeakerExperiences,
    SpeakerProfile,
    SpeakerSkillTag,
    SpeakerSocialLinks,
)


class SpeakerSocialLinksSerializer(ModelSerializer):
    """speaker social links serializers."""

    class Meta:
        """meta options."""

        model = SpeakerSocialLinks
        exclude = ["created_at", "updated_at", "speaker"]


class SpeakerSkillTagSerializer(ModelSerializer):
    """speaker skill tag serializers."""

    class Meta:
        """meta options."""

        model = SpeakerSkillTag
        exclude = ["created_at", "updated_at"]


class SpeakerExperiencesSerializer(ModelSerializer):
    """speaker experiences serializer."""

    class Meta:
        """meta options."""

        model = SpeakerExperiences
        exclude = ["created_at", "updated_at"]

    def create(self, validated_data):
        """Create speaker experience with validation."""
        event_date = validated_data.get("event_date")
        print(validated_data)
        if event_date is None:
            raise ValidationError("Event date is required.")
        speaker = self.context["request"].user.speakers_profile_user.first()
        validated_data["speaker"] = speaker
        return super().create(validated_data)


class SpeakerProfileSerializer(WritableNestedModelSerializer):
    """speaker profile serializers."""

    social_links = SpeakerSocialLinksSerializer(many=True, required=False)
    skill_tag = SpeakerSkillTagSerializer(many=True, required=False)
    speaker_name = SerializerMethodField()
    experiences = SpeakerExperiencesSerializer(
        many=True, read_only=True, required=False
    )

    class Meta:
        """meta options."""

        model = SpeakerProfile
        exclude = ["created_at", "updated_at"]

    def get_speaker_name(self, obj):
        """Get speaker name."""
        return (
            obj.user_account.first_name + " " + obj.user_account.last_name
            if obj.user_account.first_name and obj.user_account.last_name
            else obj.user_account.username
        )
