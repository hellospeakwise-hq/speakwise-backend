"""speaker serializers."""

from django.db.models import Avg
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from speakers.models import (
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


class SpeakerProfileSerializer(WritableNestedModelSerializer):
    """speaker profile serializers."""

    social_links = SpeakerSocialLinksSerializer(many=True, required=False)
    skill_tag = SpeakerSkillTagSerializer(many=True, required=False)
    speaker_name = SerializerMethodField()
    average_rating = SerializerMethodField()
    review_count = SerializerMethodField()

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

    def get_average_rating(self, obj):
        """Calculate average rating from feedback."""
        result = obj.speaker_feedback.aggregate(Avg("overall_rating"))
        avg = result["overall_rating__avg"]
        return round(avg, 1) if avg else 0.0

    def get_review_count(self, obj):
        """Get total number of reviews/feedback."""
        return obj.speaker_feedback.count()
