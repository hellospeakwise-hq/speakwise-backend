"""Serializers for the events app."""

from rest_framework import serializers

from events.models import Event
from events.services.event_import.exceptions import EventImportError
from events.services.event_import.images import download_import_image


class EventImageImportMixin(serializers.Serializer):
    """Accept a signed token for an image discovered by event import.

    A user-uploaded image always wins; the token is only resolved when no file
    was submitted. Resolution happens before the event row is created so a
    failed download never leaves a half-created event behind.
    """

    event_image_token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=4096,
        help_text=(
            "Signed token returned by the event import preview when a page "
            "image was found. Ignored when event_image is uploaded."
        ),
    )

    def create(self, validated_data):
        """Attach the imported image, then create the event."""
        token = (validated_data.pop("event_image_token", "") or "").strip()
        if token and not validated_data.get("event_image"):
            request = self.context.get("request")
            if request is None:
                raise serializers.ValidationError(
                    {"event_image_token": "No request context is available."}
                )
            try:
                validated_data["event_image"] = download_import_image(
                    token, request.user.pk
                )
            except EventImportError as exc:
                raise serializers.ValidationError(
                    {"event_image_token": str(exc)}
                ) from exc
        return super().create(validated_data)


def validate_event_is_not_duplicate(title, *, website, exclude_id=None):
    """Raise ValidationError if an event with the same name and website exists."""
    if Event.objects.find_duplicate(
        title=title, website=website or "", exclude_id=exclude_id
    ):
        raise serializers.ValidationError(
            "An event with this name and official website already exists."
        )


def validate_event_ticket_status(attrs, *, instance):
    """Require new event listings to declare free or paid admission."""
    if instance is None and attrs.get("is_free") is None:
        raise serializers.ValidationError(
            {"is_free": "Choose whether this event is free or ticketed."}
        )


class EventSerializer(EventImageImportMixin, serializers.ModelSerializer):
    """Serializer for the Event model."""

    date = serializers.SerializerMethodField()
    date_range = serializers.SerializerMethodField()
    is_cfp_currently_open = serializers.BooleanField(read_only=True)

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
        validate_event_ticket_status(attrs, instance=self.instance)
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


class EventSubmitSerializer(EventImageImportMixin, serializers.ModelSerializer):
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
            "event_image_token",
            "description",
            "website",
            "cfp_open",
            "cfp_open_date",
            "cfp_deadline",
            "cfp_speaker_notification_date",
            "cfp_link",
            "location",
            "country",
            "is_free",
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
        validate_event_ticket_status(attrs, instance=self.instance)
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


class EventImportRequestSerializer(serializers.Serializer):
    """Request shape for POST /api/events/import/preview/."""

    url = serializers.URLField(
        max_length=2048,
        help_text="Public event page URL (for example an Eventbrite or Luma page).",
    )


class EventImportDraftSerializer(serializers.Serializer):
    """Read shape for a draft event extracted from an external page.

    Field names match EventSubmitSerializer so the review form can prefill the
    existing submission form without translation.
    """

    title = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    website = serializers.CharField(allow_null=True)
    start_date_time = serializers.DateTimeField(allow_null=True)
    end_date_time = serializers.DateTimeField(allow_null=True)
    location = serializers.CharField(allow_null=True)
    country = serializers.CharField(allow_null=True)
    is_free = serializers.BooleanField(allow_null=True)
    event_image_url = serializers.CharField(allow_null=True)


class EventImportWarningSerializer(serializers.Serializer):
    """A stable, machine-readable warning about an import preview."""

    code = serializers.CharField()
    message = serializers.CharField()


class EventImportPreviewSerializer(serializers.Serializer):
    """Read shape for POST /api/events/import/preview/ responses."""

    source_url = serializers.URLField()
    platform = serializers.CharField()
    fetched_at = serializers.DateTimeField()
    draft = EventImportDraftSerializer()
    # field_sources = serializers.DictField(child=serializers.CharField())
    missing_fields = serializers.ListField(child=serializers.CharField())
    warnings = EventImportWarningSerializer(many=True)
    event_image_token = serializers.CharField(allow_null=True)
