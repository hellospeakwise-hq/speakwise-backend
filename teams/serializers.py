"""team serializers."""

from rest_framework import serializers

from teams.models import TeamMember, TeamSocial


class TeamSocialSerializer(serializers.ModelSerializer):
    """Serializer for the TeamSocial model."""

    class Meta:
        """meta options."""

        model = TeamSocial
        fields = ["name", "link"]


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for the TeamMember model."""

    avatar_url = serializers.SerializerMethodField()
    social_links = TeamSocialSerializer(many=True, read_only=True)

    class Meta:
        """meta options."""

        model = TeamMember
        exclude = ["is_active", "created_at", "updated_at"]

    def get_avatar_url(self, obj):
        """Get the full URL for the avatar image."""
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
