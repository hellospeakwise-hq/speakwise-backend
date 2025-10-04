"""Serializers for the events app."""

import base64

from django.core.files.base import ContentFile
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from events.models import Country, Event, Location, Tag
from organizations.models import Organization
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
    tags = TagSerializer(many=True, read_only=True)
    website = serializers.URLField(required=False, allow_blank=True)
    short_description = serializers.CharField(required=False, allow_blank=True)
    location = LocationSerializer(required=False)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    # User permissions
    can_user_manage = serializers.SerializerMethodField()

    # Frontend-specific computed fields
    name = serializers.CharField(source="title", read_only=True)
    date = serializers.SerializerMethodField()
    date_range = serializers.SerializerMethodField()  # New field for start/end dates

    class Meta:
        """Meta class for the EventSerializer."""

        model = Event
        exclude = ["created_at", "updated_at"]

    def get_can_user_manage(self, obj):
        """Check if current user can manage this event."""
        request = self.context.get("request")
        if (
            not request
            or not hasattr(request, "user")
            or not request.user.is_authenticated
        ):
            return False
        return obj.can_user_manage(request.user)

    def create(self, validated_data):
        """Create event with proper organization/organizer assignment."""
        organization = validated_data.pop("organization", None)

        # Validate organization permissions
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            try:
                organization = Organization.objects.get(id=organization.id)
                # Check if user can create events for this organization
                if not organization.organization_memberships.filter(
                    user=request.user, is_active=True, can_manage_events=True
                ).exists():
                    raise serializers.ValidationError(
                        "You don't have permission to create events for this organization."
                    )
                validated_data["organization"] = organization
            except Organization.DoesNotExist:
                raise serializers.ValidationError(
                    {"detail": "Organization not found."}
                ) from None

        return super().create(validated_data)

    def get_date(self, obj):
        """Format date range for frontend display - keeping for backward compatibility."""
        if obj.start_date_time and obj.end_date_time:
            start_date = obj.start_date_time.strftime("%B %d")
            end_date = obj.end_date_time.strftime("%d, %Y")

            # Check if same month/year
            if (
                obj.start_date_time.month == obj.end_date_time.month
                and obj.start_date_time.year == obj.end_date_time.year
            ):
                if obj.start_date_time.day == obj.end_date_time.day:
                    # Same day
                    return obj.start_date_time.strftime("%B %d, %Y")
                # Same month, different days
                return f"{start_date}-{end_date}"
            # Different months/years
            start_full = obj.start_date_time.strftime("%B %d, %Y")
            end_full = obj.end_date_time.strftime("%B %d, %Y")
            return f"{start_full} - {end_full}"
        return None

    def get_date_range(self, obj):
        """Get separate start and end dates for better display control."""
        if not obj.start_date_time or not obj.end_date_time:
            return {"start": None, "end": None, "same_day": False}

        start_date = obj.start_date_time.strftime("%B %d, %Y")
        start_time = obj.start_date_time.strftime("%I:%M %p")
        end_date = obj.end_date_time.strftime("%B %d, %Y")
        end_time = obj.end_date_time.strftime("%I:%M %p")

        same_day = (
            obj.start_date_time.year == obj.end_date_time.year
            and obj.start_date_time.month == obj.end_date_time.month
            and obj.start_date_time.day == obj.end_date_time.day
        )

        return {
            "start": {
                "date": start_date,
                "time": start_time,
                "datetime": obj.start_date_time.isoformat(),
            },
            "end": {
                "date": end_date,
                "time": end_time,
                "datetime": obj.end_date_time.isoformat(),
            },
            "same_day": same_day,
        }

    def to_internal_value(self, data):
        """Handle base64 image encoding."""
        if data.get("event_image") and ";base64," in data["event_image"]:
            img_format, imgstr = data["event_image"].split(";base64,")
            ext = img_format.split("/")[-1]
            data["event_image"] = ContentFile(
                base64.b64decode(imgstr),
                name=f"temp.{ext}",
            )
        return super().to_internal_value(data)

    def get_attendees(self, obj):
        """Return attendees for this event. No model linked yet, so empty list."""
        return []

    def get_speakers(self, obj):
        """Return unique speaker profiles from the event's sessions."""
        speakers = []
        seen = set()
        for s in obj.sessions.select_related("speaker").all():
            if s.speaker and s.speaker.id not in seen:
                seen.add(s.speaker.id)
                speakers.append(s.speaker)
        return SpeakerProfileSerializer(speakers, many=True).data


class EventWithGuestSpeakersSerializer(EventSerializer):
    """Extended Event serializer that includes full speaker profile data."""

    speaker_profiles = serializers.SerializerMethodField()
    event_sessions = serializers.SerializerMethodField()

    def get_speaker_profiles(self, obj):
        """Get detailed speaker profiles for this event."""
        speakers = obj.speakers.all()
        return SpeakerProfileSerializer(speakers, many=True).data
