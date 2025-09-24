"""organizers admin."""

from django.contrib import admin

from organizers.models import OrganizerProfile, OrganizerSocialLinks


@admin.register(OrganizerSocialLinks)
class OrganizerSocialAdmin(admin.ModelAdmin):
    """organizer profile admin model."""

    list_display = ["name", "link"]
    search_fields = ["name"]
    list_filter = ["name"]


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    """organizer profile admin model."""

    list_display = ["user_account", "organization", "country"]
    search_fields = ["user_account", "organization", "country"]
    list_filter = ["user_account", "organization", "country"]
