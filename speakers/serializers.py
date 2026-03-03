"""speaker serializers."""

from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework.exceptions import ValidationError
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


class FollowerDetailSerializer(ModelSerializer):
    """Rich serializer returning speaker profile info for followers/following lists."""

    username = SerializerMethodField()
    full_name = SerializerMethodField()
    avatar = SerializerMethodField()
    slug = SerializerMethodField()
    short_bio = SerializerMethodField()
    country = SerializerMethodField()
    organization = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerFollow
        fields = [
            "id",
            "username",
            "full_name",
            "avatar",
            "slug",
            "short_bio",
            "country",
            "organization",
            "created_at",
        ]

    def _get_profile(self, user):
        """Get the SpeakerProfile for a user, if it exists."""
        return SpeakerProfile.objects.filter(user_account=user).first()

    def _get_user(self, obj):
        """Get the relevant user depending on context (follower or following)."""
        context_type = self.context.get("type", "followers")
        if context_type == "following":
            return obj.speaker.user_account
        return obj.follower

    def get_username(self, obj) -> str:
        """Return the username."""
        return self._get_user(obj).username

    def get_full_name(self, obj) -> str:
        """Return the full name (None-safe)."""
        user = self._get_user(obj)
        first = (user.first_name or "").strip()
        last = (user.last_name or "").strip()
        full = f"{first} {last}".strip()
        return full or user.username

    def get_avatar(self, obj):
        """Return the avatar URL."""
        profile = self._get_profile(self._get_user(obj))
        if profile and profile.avatar:
            return profile.avatar.url
        return None

    def get_slug(self, obj):
        """Return the speaker profile slug."""
        profile = self._get_profile(self._get_user(obj))
        return profile.slug if profile else None

    def get_short_bio(self, obj) -> str:
        """Return the short bio."""
        profile = self._get_profile(self._get_user(obj))
        return profile.short_bio if profile else ""

    def get_country(self, obj) -> str:
        """Return the country."""
        profile = self._get_profile(self._get_user(obj))
        return profile.country if profile else ""

    def get_organization(self, obj) -> str:
        """Return the organization."""
        profile = self._get_profile(self._get_user(obj))
        return profile.organization if profile else ""


class SpeakerProfileSerializer(WritableNestedModelSerializer):
    """speaker profile serializers."""

    social_links = SpeakerSocialLinksSerializer(many=True, required=False)
    skill_tags = SpeakerSkillTagSerializer(many=True, required=False)
    speaker_name = SerializerMethodField()
    experiences = SpeakerExperiencesSerializer(
        many=True, read_only=True, required=False
    )
    followers_count = SerializerMethodField()
    following_count = SerializerMethodField()
    is_following = SerializerMethodField()

    class Meta:
        """meta options."""

        model = SpeakerProfile
        exclude = ["created_at", "updated_at"]
        read_only_fields = ("slug", "user_account")

    @transaction.atomic
    def create(self, validated_data):
        """Create a speaker profile."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if SpeakerProfile.objects.filter(user_account=request.user).exists():
                raise ValidationError({"detail": "Speaker profile already exists for this user."})
            validated_data["user_account"] = request.user
        else:
            raise ValidationError({"detail": "Must be authenticated to create a profile."})

        return super().create(validated_data)

    def get_speaker_name(self, obj) -> str:
        """Get speaker name."""
        first = (obj.user_account.first_name or "").strip()
        last = (obj.user_account.last_name or "").strip()
        full = f"{first} {last}".strip()
        return full if full else obj.user_account.username

    def get_followers_count(self, obj) -> int:
        """Return total number of followers for this speaker."""
        return obj.followers_count

    def get_following_count(self, obj) -> int:
        """Return how many speakers this speaker follows (their following count)."""
        return SpeakerFollow.objects.filter(follower=obj.user_account).count()

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

        instance = super().update(instance, validated_data)
        # NOTE: skill_tags nested updates are handled automatically by
        # WritableNestedModelSerializer via update_or_create_reverse_relations().
        # No manual loop needed here.

        for item in social_data:
            link_id = item.get("id")
            if link_id:
                SpeakerSocialLinks.objects.filter(id=link_id, speaker=instance).update(
                    **{k: v for k, v in item.items() if k != "id"}
                )
            else:
                SpeakerSocialLinks.objects.create(speaker=instance, **item)

        return instance
