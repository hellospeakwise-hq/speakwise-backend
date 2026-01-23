"""event admin."""

from django.contrib import admin

from events.models import Country, Event, Location, Tag


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin configuration for the Event model."""

    list_display = ("title", "organizer", "start_date_time", "is_active")
    list_filter = ("is_active", "organizer", "tags")
    search_fields = ("title", "description")
    raw_id_fields = ("organizer", "location")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin configuration for the Location model."""

    list_display = ("venue", "city", "country")
    search_fields = ("venue", "city", "address")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for the Tag model."""

    list_display = ("name", "color")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin configuration for the Country model."""

    list_display = ("name", "code")
