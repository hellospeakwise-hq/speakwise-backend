"""sessions admin."""

from django.contrib import admin

from eventsessions.models import (
    Session,
    SessionSpeaker,
    SessionSponsor,
    SessionVenue,
    Track,
)


@admin.register(SessionVenue)
class SessionVenueAdmin(admin.ModelAdmin):
    """session venue admin."""

    list_display = ("name", "capacity", "virtual_url")
    search_fields = ("name",)
    list_filter = ("capacity",)


@admin.register(SessionSponsor)
class SessionSponsorAdmin(admin.ModelAdmin):
    """session sponsor admin."""

    list_display = ("session", "sponsor")
    search_fields = ("session__title", "sponsor__name")
    list_filter = ("sponsor",)


@admin.register(SessionSpeaker)
class SessionSpeakerAdmin(admin.ModelAdmin):
    """session speaker admin."""

    list_display = ("session", "speaker")
    search_fields = ("session__title", "speaker__name")
    list_filter = ("speaker",)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    """track admin."""

    list_display = ("name", "description")
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """session admin."""

    list_display = ("title", "event", "start_time", "end_time")
    search_fields = ("title", "event__name")
    list_filter = ("event", "track")
