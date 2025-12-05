"""Admin configuration for the feedback app."""

from django.contrib import admin

from feedbacks.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback model."""

    list_display = [
        "id",
        "session",
        "speaker",
        "overall_rating",
        "is_anonymous",
        "created_at",
    ]
    list_filter = ["is_anonymous", "is_attendee", "created_at"]
    search_fields = ["speaker__user__email", "comments"]
    raw_id_fields = ["session", "speaker"]
