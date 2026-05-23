"""Events schedule admin."""

from django.contrib import admin

from eventschedules.models import EventSchedule


@admin.register(EventSchedule)
class EventScheduleAdmin(admin.ModelAdmin):
    """Admin for EventSchedule."""

    list_display = ["id", "event", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["event"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    filter_horizontal = ["sessions"]
