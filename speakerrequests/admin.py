"""speaker request admin."""

from django.contrib import admin

from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest


@admin.register(SpeakerRequest)
class SpeakerRequestAdmin(admin.ModelAdmin):
    """Admin for SpeakerRequest model."""

    list_display = ("event", "requested_by", "organization")
    search_fields = (
        "event",
        "message",
    )


@admin.register(SpeakerEmailRequests)
class SpeakerEmailRequestsAdmin(admin.ModelAdmin):
    """Admin for SpeakerEmailRequests model."""

    list_display = ("id", "request_from", "event")
    search_fields = (
        "request__request_from__username",
        "request__request_to__username",
        "request__event",
        "request__location",
        "request__message",
    )
