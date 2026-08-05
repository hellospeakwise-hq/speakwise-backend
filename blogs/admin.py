"""blogs admin."""

from django.contrib import admin

from blogs.models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    """Admin configuration for the Blog model."""

    list_display = (
        "title",
        "created_by",
        "published_date",
        "created_at",
    )
    search_fields = ("title", "short_description")
    list_filter = ("published_date",)
