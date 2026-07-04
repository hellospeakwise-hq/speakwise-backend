"""event schedule serializers."""

from rest_framework import serializers

from eventsessions.serializers import SessionSerializer

from .models import EventSchedule


class EventScheduleSerializer(serializers.ModelSerializer):
    """Event schedule serializer."""

    sessions = SessionSerializer(many=True, read_only=True)

    class Meta:
        """metaclass."""

        model = EventSchedule
        exclude = ["created_at", "updated_at"]
        read_only_fields = ("id",)
