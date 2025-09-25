"""talks admin."""

from django.contrib import admin

from talks.models import Session, Talks


@admin.register(Talks)
class TalkAdmin(admin.ModelAdmin):
    """talk admin."""

    list_display = ("title", "speaker", "category", "duration")
    list_filter = ["speaker", "category"]
    search_fields = (
        "title",
        "category",
    )


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """session admin."""

    list_display = ("talk", "type", "duration")
    list_filter = ("talk", "type")
    search_fields = ("title", "talk")
