"""event admin."""

from django.contrib import admin

from events.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for reviewing listed events and CFP open/closed configuration."""

    list_display = (
        "title",
        "is_featured",
        "is_active",
        "website",
        "submitted_by",
        "start_date_time",
        "end_date_time",
    )
    list_editable = ("is_featured", "is_active")
    list_filter = ("is_featured", "is_active", "country")
    search_fields = (
        "title",
        "website",
        "cfp_link",
        "slug",
    )
    readonly_fields = ("id", "submitted_by", "slug", "created_at", "updated_at")
