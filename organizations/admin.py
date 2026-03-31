"""Admin configuration for organizations app."""

from django.contrib import admin

from organizations.models import Organization, OrganizationMembership


# Register your models here.
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """organization admin configuration."""

    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "owner__username")
    list_filter = ("created_at", "updated_at")


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """OrganizationMembership admin configuration."""

    list_display = ("user", "organization", "role", "created_at", "updated_at")
    search_fields = ("user__username", "organization__name")
    list_filter = ("role", "created_at", "updated_at")
