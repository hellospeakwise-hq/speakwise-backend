"""event admin."""

from django.contrib import admin

from events.models import Country, Event, Location, Tag


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    """Admin for reviewing listed events and CFP open/closed configuration."""
=======
    """Admin configuration for reviewing and publishing events."""
>>>>>>> f0bbdb6e (Enhance event management with admin configuration, improved model queries, and submission workflow. Added event approval process, duplicate detection, and serializers for community submissions. Updated views and tests for new functionality.)

    list_display = (
        "title",
        "website",
        "is_active",
        "submitted_by",
<<<<<<< HEAD
        "accepts_cfp",
        "cfp_open",
        "cfp_deadline",
        "start_date_time",
    )
    list_filter = ("is_active", "accepts_cfp", "cfp_open")
    search_fields = (
        "title",
        "website",
        "cfp_url",
        "cfp_link",
        "slug",
        "short_description",
    )
    readonly_fields = ("id", "submitted_by", "slug", "created_at", "updated_at")
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
                    "cfp_url",
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
=======
        "start_date_time",
    )
    list_filter = ("is_active",)
    search_fields = ("title", "website", "cfp_url")
    readonly_fields = ("submitted_by", "slug")
>>>>>>> f0bbdb6e (Enhance event management with admin configuration, improved model queries, and submission workflow. Added event approval process, duplicate detection, and serializers for community submissions. Updated views and tests for new functionality.)


admin.site.register(Country)
admin.site.register(Tag)
admin.site.register(Location)
