"""Serializers for the events app."""

from typing import Any

from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from events.models import Country, Event, Location, Tag
from speakers.serializers import SpeakerProfileSerializer


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for the Country model."""

    class Meta:
        """Meta class for the CountrySerializer."""

        model = Country
        exclude = ["created_at", "updated_at"]


class LocationSerializer(WritableNestedModelSerializer):
    """Serializer for the Region model."""

    country = CountrySerializer(required=False)

    class Meta:
        """Meta class for the RegionSerializer."""

        model = Location
        exclude = ("created_at", "updated_at")


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the Tag model."""

    class Meta:
        """Meta class for the TagSerializer."""

        model = Tag
        exclude = ["created_at", "updated_at"]


class EventSerializer(WritableNestedModelSerializer):
    """Serializer for the Event model."""

    event_image = serializers.ImageField(required=False, allow_null=True)
    tags = TagSerializer(many=True, required=False)
    website = serializers.URLField(required=False, allow_blank=True)
    short_description = serializers.CharField(required=False, allow_blank=True)
    location = LocationSerializer(required=False)
    # Frontend-specific computed fields
    name = serializers.CharField(source="title", read_only=True)
    date = serializers.SerializerMethodField()
    date_range = serializers.SerializerMethodField()  # New field for start/end dates

    class Meta:
        """Meta class for the EventSerializer."""

        model = Event
        exclude = ["created_at", "updated_at"]

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


class EventWithGuestSpeakersSerializer(EventSerializer):
    """Extended Event serializer that includes full speaker profile data."""

    speaker_profiles = serializers.SerializerMethodField()
    event_sessions = serializers.SerializerMethodField()

    def get_speaker_profiles(self, obj) -> list[dict]:
        """Get detailed speaker profiles for this event."""
        speakers = obj.speakers.all()
        return SpeakerProfileSerializer(speakers, many=True).data
