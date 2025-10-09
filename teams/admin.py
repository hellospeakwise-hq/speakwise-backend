"""teams admin configuration."""

from django.contrib import admin

from teams.models import TeamMember, TeamSocial


class TeamSocialInline(admin.TabularInline):
    """Inline admin for managing social links on a Team Member."""

    model = TeamSocial
    extra = 1


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin configuration for Team Member model."""

    list_display = ("name", "role", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "role")
    inlines = [TeamSocialInline]


# admin.site.register(TeamSocial)
