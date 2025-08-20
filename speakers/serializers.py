"""speaker serializers."""

from rest_framework.serializers import ModelSerializer
from drf_writable_nested.serializers import WritableNestedModelSerializer
from speakers.models import SpeakerProfile, SpeakerSocialLinks, SpeakerSkillTag


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
    skill_tags = SpeakerSkillTagSerializer(many=True, required=False)

    class Meta:
        """meta options."""

        model = SpeakerProfile
        exclude = ["created_at", "updated_at"]
