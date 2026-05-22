"""event schedule serializers."""

from rest_framework import serializers

from eventsessions.serializers import SessionSerializer

from .models import EventSchedule


class EventScheduleSerializer(serializers.ModelSerializer):
    """Event schedule serializer."""

    session = SessionSerializer(many=True, read_only=True)

    class Meta:
        """metaclass."""

        model = EventSchedule
        exclude = ["created_at", "updated_at"]
        read_only_fields = ("id",)

    def validate(self, attrs):
        """Validate event schedule data."""
        event = self.context.get("event")
        session = attrs.get("session")

        if event and session and session.event != event:
            raise serializers.ValidationError(
                {"session": "Session must belong to the event."}
            )

        return attrs
