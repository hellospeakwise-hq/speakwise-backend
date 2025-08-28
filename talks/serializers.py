"""talks serializers."""

from rest_framework import serializers

from talks.models import Talks


class TalkSerializer(serializers.ModelSerializer):
    """Serializer for Talk model."""

    class Meta:
        """meta options."""

        model = Talks
        exclude = ("created_at", "updated_at")
