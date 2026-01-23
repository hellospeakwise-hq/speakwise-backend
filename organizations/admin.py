"""Admin configuration for organizations app."""

from django.contrib import admin

from organizations.models import Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for the Organization model."""

    list_display = ("name", "email", "website", "is_active", "created_by")
    list_filter = ("is_active",)
    search_fields = ("name", "email", "description")
    raw_id_fields = ("created_by",)


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for the OrganizationMembership model."""

    list_display = ("user", "organization", "role", "is_active")
    list_filter = ("role", "is_active", "organization")
    search_fields = ("user__username", "user__email", "organization__name")
    raw_id_fields = ("user", "organization", "added_by")
