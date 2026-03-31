"""Serializers for the events app."""

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
        validators = []
        extra_kwargs = {
            "name": {"validators": []}, 
            "code": {"validators": []},
        }

    def create(self, validated_data):
        """Get or create a Country by name (and optionally code)."""
        name = validated_data.get("name")
        code = validated_data.get("code")
        lookup = {}
        if name:
            lookup["name"] = name
        if code and not name:
            lookup["code"] = code
        if lookup:
            country, _ = Country.objects.get_or_create(
                **lookup,
                defaults=validated_data,
            )
            return country
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a Country, or return an existing one if name/code matches."""
        name = validated_data.get("name", instance.name)
        # If name changed to one that already exists, return that existing record
        if name and name != instance.name:
            existing = Country.objects.filter(name=name).first()
            if existing and existing.pk != instance.pk:
                return existing
        return super().update(instance, validated_data)


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


def _resolve_location(location_data: dict | None) -> Location | None:
    """
    Handles the Country nested inside location using get_or_create so that
    picking an already-existing country never raises a unique-constraint error.
    """
    if not location_data:
        return None

    country_data = location_data.pop("country", None)
    country = None

    if country_data:
        name = country_data.get("name")
        code = country_data.get("code")
        lookup = {}
        if name:
            lookup["name"] = name
        elif code:
            lookup["code"] = code

        if lookup:
            country, _ = Country.objects.get_or_create(
                **lookup, defaults=country_data
            )

    # Build location lookup fields (everything except country and the PK)
    city = location_data.get("city", "")
    venue = location_data.get("venue", "")
    postal_code = location_data.get("postal_code", "")
    address = location_data.get("address", "")

    # Try to find an existing location that matches country + city + venue
    existing_qs = Location.objects.filter(country=country, city=city, venue=venue)
    if existing_qs.exists():
        location = existing_qs.first()
        # Update mutable fields in case they changed
        location.postal_code = postal_code
        location.address = address
        location.save(update_fields=["postal_code", "address"])
        return location

    # Create a new location
    return Location.objects.create(
        country=country,
        city=city,
        venue=venue,
        postal_code=postal_code,
        address=address,
    )


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

    # ------------------------------------------------------------------
    # Override create/update to resolve location → country via get_or_create
    # instead of letting drf_writable_nested blindly try to INSERT a country
    # that already exists.
    # ------------------------------------------------------------------

    def create(self, validated_data):
        location_data = validated_data.pop("location", None)
        location = _resolve_location(location_data)
        if location:
            validated_data["location"] = location
        return super().create(validated_data)

    def update(self, instance, validated_data):
        location_data = validated_data.pop("location", None)
        if location_data is not None:
            location = _resolve_location(location_data)
            if location:
                validated_data["location"] = location
        return super().update(instance, validated_data)

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
