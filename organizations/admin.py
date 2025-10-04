"""Admin configuration for organizations."""

from django.contrib import admin

from .models import Organization, OrganizationMembership


class OrganizationMembershipInline(admin.TabularInline):
    """Inline admin for organization memberships."""

    model = OrganizationMembership
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "user",
        "role",
        "added_by",
        "is_active",
        "can_review_talks",
        "can_manage_events",
        "can_add_organizers",
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for Organization model."""

    list_display = (
        "name",
        "email",
        "created_by",
        "is_active",
        "member_count",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "email", "description")
    readonly_fields = ("created_at", "updated_at", "member_count", "admin_count")
    inlines = [OrganizationMembershipInline]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "description", "email", "website", "logo")},
        ),
        ("Status", {"fields": ("is_active", "created_by")}),
        (
            "Statistics",
            {"fields": ("member_count", "admin_count"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Active Members")
    def member_count(self, obj):
        """Get member count for admin display."""
        return obj.organization_memberships.filter(is_active=True).count()

    @admin.display(description="Admins")
    def admin_count(self, obj):
        """Get admin count for admin display."""
        return obj.organization_memberships.filter(role="admin", is_active=True).count()


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for OrganizationMembership model."""

    list_display = (
        "user",
        "organization",
        "role",
        "is_active",
        "added_by",
        "created_at",
    )
    list_filter = (
        "role",
        "is_active",
        "can_review_talks",
        "can_manage_events",
        "can_add_organizers",
    )
    search_fields = ("user__username", "user__email", "organization__name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Membership Details",
            {"fields": ("organization", "user", "role", "added_by", "is_active")},
        ),
        (
            "Permissions",
            {"fields": ("can_review_talks", "can_manage_events", "can_add_organizers")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
