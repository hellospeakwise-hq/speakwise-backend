"""event admin."""

from django.contrib import admin

from events.models import Country, Event, Location, Tag


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin configuration for reviewing and publishing events."""

    list_display = (
        "title",
        "website",
        "is_active",
        "submitted_by",
        "start_date_time",
    )
    list_filter = ("is_active",)
    search_fields = ("title", "website", "cfp_url")
    readonly_fields = ("submitted_by", "slug")


admin.site.register(Country)
admin.site.register(Tag)
admin.site.register(Location)
