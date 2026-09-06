"""Serializers for the events app."""

from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from events.models import Event


def validate_event_is_not_duplicate(title, *, website, exclude_id=None):
    """Raise ValidationError if an event with the same name and website exists."""
    if Event.objects.find_duplicate(
        title=title, website=website or "", exclude_id=exclude_id
    ):
        raise serializers.ValidationError(
            "An event with this name and official website already exists."
        )


class EventSerializer(WritableNestedModelSerializer):
    """Serializer for the Event model."""

    class Meta:
        """Meta class for the EventSerializer."""

        model = Event
        exclude = ["created_at", "updated_at"]

    def validate(self, attrs):
        """Reject listings that duplicate an existing name and official website."""
        title = attrs.get("title") or (self.instance.title if self.instance else "")
        website = attrs.get("website")
        if website is None:
            website = self.instance.website if self.instance else ""
        exclude_id = self.instance.pk if self.instance else None
        validate_event_is_not_duplicate(
            title=title, website=website or "", exclude_id=exclude_id
        )
        return attrs

    def get_date(self, obj) -> str | None:
        """Return a compact date representation for the event.

        - If start and end fall on the same date, return the ISO date string for that day.
        - If they span multiple days, return a human-friendly range string.
        - If only a start is present, return its ISO date.
        """
        start = obj.start_date_time
        end = obj.end_date_time
        if start and end:
            try:
                if start.date() == end.date():
                    return start.date().isoformat()
                return f"{start.date().isoformat()} to {end.date().isoformat()}"
            except Exception:
                # Fallback to isoformat for datetimes if date() access fails
                return f"{start.isoformat()} to {end.isoformat()}"
        if start:
            return start.date().isoformat()
        return None

    def get_date_range(self, obj) -> dict:
        """Return start/end datetimes for the event in ISO format."""
        start = obj.start_date_time
        end = obj.end_date_time
        return {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        }


class EventSubmitSerializer(serializers.ModelSerializer):
    """Serializer for community event submissions to the public listing.

    Captures showcase fields only. Internal CFP submission settings are not
    accepted here — those belong to the separate CFP process.
    """

    class Meta:
        """Meta class for the EventSubmitSerializer."""

        model = Event
        fields = [
            "id",
            "title",
            "event_nickname",
            "event_image",
            "description",
            "website",
            "cfp_open",
            "cfp_open_date",
            "cfp_deadline",
            "cfp_speaker_notification_date",
            "cfp_link",
            "location",
            "start_date_time",
            "end_date_time",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Reject submissions that duplicate an existing listing."""
        validate_event_is_not_duplicate(
            title=attrs.get("title", ""),
            website=attrs.get("website", ""),
        )
        return attrs

    def create(self, validated_data):
        """Create a pending event listing from a user submission."""
        return super().create(validated_data)


class CFPMarketSerializer(serializers.ModelSerializer):
    """Slim serializer for CFP Market cards listing open CFPs."""

    name = serializers.CharField(source="title", read_only=True)
    is_cfp_currently_open = serializers.BooleanField(read_only=True)

    class Meta:
        """Meta options for CFPMarketSerializer."""

        model = Event
        fields = [
            "id",
            "slug",
            "title",
            "name",
            "event_image",
            "cfp_open",
            "cfp_link",
            "cfp_deadline",
            "cfp_open_date",
            "is_cfp_currently_open",
        ]
