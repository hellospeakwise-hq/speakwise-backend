"""event schedule serializers."""

from rest_framework import serializers

from .models import EventSchedule


class EventScheduleSerializer(serializers.ModelSerializer):
    """Event schedule serializer."""

    class Meta:
        """metaclass."""

        model = EventSchedule
        exclude = ["created_at", "updated_at"]
        read_only_fields = ("id",)
