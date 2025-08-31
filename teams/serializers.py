from teams.models import TeamMember, TeamSocial
from rest_framework import serializers


class TeamSocialSerializer(serializers.ModelSerializer):
    """Serializer for the TeamSocial model."""

    class Meta:
        model = TeamSocial
        fields = ["name", "link"]


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for the TeamMember model."""

    avatar_url = serializers.SerializerMethodField()
    social_links = TeamSocialSerializer(many=True, read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "name", "role", "short_bio", "avatar", "avatar_url", "display_order", "social_links"]

    def get_avatar_url(self, obj):
        """Get the full URL for the avatar image."""
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None