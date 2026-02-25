"""speaker serializers."""

from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from jsonschema import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from speakers.models import (
    SpeakerExperiences,
    SpeakerFollow,
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
        exclude = ["created_at", "updated_at", "speaker"]


class SpeakerExperiencesSerializer(ModelSerializer):
    """speaker experiences serializer."""

    class Meta:
        """meta options."""

        model = SpeakerExperiences
        exclude = ["created_at", "updated_at"]

    def create(self, validated_data) -> SpeakerExperiences:
        """Create speaker experience with validation."""
        event_date = validated_data.get("event_date")
        if event_date is None:
            raise ValidationError("Event date is required.")
        speaker = self.context["request"].user.speakers_profile_user.first()
        validated_data["speaker"] = speaker
        return super().create(validated_data)


class SpeakerFollowSerializer(ModelSerializer):
    """Serializer for the SpeakerFollow model."""

    follower_username = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerFollow
        fields = ["id", "follower", "follower_username", "created_at"]
        read_only_fields = ["id", "follower", "follower_username", "created_at"]

    def get_follower_username(self, obj) -> str:
        """Return the username of the follower."""
        return obj.follower.username


class SpeakerProfileSerializer(WritableNestedModelSerializer):
    """speaker profile serializers."""

    social_links = SpeakerSocialLinksSerializer(many=True, required=False)
    skill_tags = SpeakerSkillTagSerializer(many=True, required=False)
    speaker_name = SerializerMethodField()
    experiences = SpeakerExperiencesSerializer(
        many=True, read_only=True, required=False
    )
    followers_count = SerializerMethodField()
    is_following = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerProfile
        exclude = ["created_at", "updated_at"]
        read_only_fields = ("slug",)

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        first = (obj.user_account.first_name or "").strip()
        last = (obj.user_account.last_name or "").strip()
        full = f"{first} {last}".strip()
        return full if full else obj.user_account.username

    def get_followers_count(self, obj) -> int:
        """Return total number of followers for this speaker."""
        return obj.followers_count

    def get_is_following(self, obj) -> bool:
        """Return True if the current authenticated user follows this speaker."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return SpeakerFollow.objects.filter(
                follower=request.user, speaker=obj
            ).exists()
        return False

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update speaker profile objects."""
        social_data = validated_data.pop("social_links", [])
        skill_data = validated_data.pop("skill_tag", [])

        instance = super().update(instance, validated_data)

        for item in skill_data:
            tag_id = item.get("id")
            if tag_id:
                SpeakerSkillTag.objects.filter(id=tag_id).update(
                    **{k: v for k, v in item.items() if k != "id"}
                )
                tag = SpeakerSkillTag.objects.get(id=tag_id)
            else:
                tag = SpeakerSkillTag.objects.create(**item)
            instance.skill_tag.add(tag)

        for item in social_data:
            link_id = item.get("id")
            if link_id:
                SpeakerSocialLinks.objects.filter(id=link_id, speaker=instance).update(
                    **{k: v for k, v in item.items() if k != "id"}
                )
            else:
                SpeakerSocialLinks.objects.create(speaker=instance, **item)

        return instance
