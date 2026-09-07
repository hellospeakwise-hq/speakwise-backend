"""event admin."""

from django.contrib import admin

from events.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for reviewing listed events and CFP open/closed configuration."""

    list_display = (
        "title",
        "website",
        "is_active",
        "submitted_by",
        "cfp_deadline",
        "start_date_time",
    )
    list_filter = ("is_active",)
    search_fields = (
        "title",
        "website",
        "cfp_link",
        "slug",
    )
    readonly_fields = ("id", "submitted_by", "slug", "created_at", "updated_at")
