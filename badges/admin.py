"""Admin registrations for badges app."""

from django.contrib import admin

from badges.choices import BadgeStatusChoices
from badges.models import BadgeDefinition, SpeakerBadge


@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    """Admin configuration for badge definitions."""

    list_display = ("token_id", "name", "tier", "metric_type", "metric_threshold")
    list_filter = ("tier", "metric_type")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SpeakerBadge)
class SpeakerBadgeAdmin(admin.ModelAdmin):
    """Admin configuration for speaker badges and claim actions."""

    list_display = (
        "speaker",
        "badge",
        "status",
        "tx_hash",
        "recipient_address",
        "claimed_at",
    )
    list_filter = ("status", "badge__tier")
    search_fields = (
        "speaker__user_account__username",
        "badge__name",
        "tx_hash",
        "recipient_address",
    )
    readonly_fields = ("unlocked_at", "claimed_at")
    actions = ["revoke_to_eligible", "revoke_and_lock"]

    @admin.action(description="Revoke claim & reset to Eligible (allows re-claiming)")
    def revoke_to_eligible(self, request, queryset):
        """Revoke a badge claim and reset status back to eligible."""
        updated = queryset.update(
            status=BadgeStatusChoices.ELIGIBLE,
            tx_hash=None,
            recipient_address=None,
            claimed_at=None,
        )
        self.message_user(
            request, f"Successfully revoked {updated} badge(s) and reset to Eligible."
        )

    @admin.action(description="Revoke & Lock badge(s)")
    def revoke_and_lock(self, request, queryset):
        """Revoke a badge claim and reset status back to locked."""
        updated = queryset.update(
            status=BadgeStatusChoices.LOCKED,
            tx_hash=None,
            recipient_address=None,
            claimed_at=None,
        )
        self.message_user(request, f"Successfully locked {updated} badge(s).")
