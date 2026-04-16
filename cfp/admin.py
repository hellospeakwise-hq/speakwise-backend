"""CFP admin."""

from django.contrib import admin

from cfp.models import CFPSubmission


@admin.register(CFPSubmission)
class CFPSubmissionAdmin(admin.ModelAdmin):
    """Admin config for CFPSubmission."""

    list_display = (
        "submitter",
        "event",
        "talk_type",
        "category",
        "status",
        "created_at",
    )
    list_filter = ("status", "talk_type", "category", "audience")
    search_fields = ("submitter__email", "event__title", "elevator_pitch")
    readonly_fields = ("id", "created_at", "updated_at")
