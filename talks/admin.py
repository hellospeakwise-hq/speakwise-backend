"""talks admin."""

from django.contrib import admin

from talks.models import Talks, TalkSession


@admin.register(Talks)
class TalkAdmin(admin.ModelAdmin):
    """talk admin."""

    list_display = ("title", "speaker", "category", "duration")
    list_filter = ["speaker", "category"]
    search_fields = (
        "title",
        "category",
    )


@admin.register(TalkSession)
class SessionAdmin(admin.ModelAdmin):
    """session admin."""

    list_display = ("talk", "session_type", "duration")
    list_filter = ("talk", "session_type")
    search_fields = ("title", "talk")
