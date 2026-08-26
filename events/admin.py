"""event admin."""

from django.contrib import admin

from events.models import Country, Event, Location, Tag


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for reviewing listed events and CFP open/closed configuration."""

    list_display = (
        "title",
        "website",
        "is_active",
        "submitted_by",
        "accepts_cfp",
        "cfp_open",
        "cfp_deadline",
        "slug",
    )
    list_filter = ("is_active", "accepts_cfp", "cfp_open")
    search_fields = (
        "title",
        "website",
        "cfp_link",
        "slug",
        "short_description",
    )
    readonly_fields = ("id", "submitted_by", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "title",
                    "event_nickname",
                    "slug",
                    "event_image",
                    "short_description",
                    "description",
                    "website",
                    "location",
                    "start_date_time",
                    "end_date_time",
                    "is_active",
                    "submitted_by",
                    "tags",
                    "speaker_deck_upload_enabled",
                )
            },
        ),
        (
            "CFP",
            {
                "fields": (
                    "accepts_cfp",
                    "cfp_open",
                    "cfp_link",
                    "cfp_description",
                    "cfp_open_date",
                    "cfp_deadline",
                    "cfp_speaker_notification_date",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


admin.site.register(Country)
admin.site.register(Tag)
admin.site.register(Location)
