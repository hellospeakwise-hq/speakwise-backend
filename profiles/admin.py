"""speakers admin."""

from django.contrib import admin

from profiles.models.organization_models import OrganizationCFP, OrganizationProfile
from profiles.models.speaker_models import (
    Notification,
    SpeakerExperiences,
    SpeakerFollow,
    SpeakerProfile,
    SpeakerSkillTag,
    SpeakerSocialLinks,
)


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    """Organization profile admin."""

    list_display = ("name", "description")
    search_fields = ("name",)
    list_filter = ("name", "owner__username")
    ordering = ("name",)


@admin.register(SpeakerProfile)
class SpeakerProfileAdmin(admin.ModelAdmin):
    """Speaker profile admin."""

    list_display = ("user_account__username",)
    search_fields = ("user_account__username",)
    list_filter = ("user_account__username",)
    ordering = ("user_account__username",)


@admin.register(SpeakerSkillTag)
class SpeakerSkillTagAdmin(admin.ModelAdmin):
    """Speaker skill tag admin."""

    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)
    ordering = ("name",)


@admin.register(SpeakerExperiences)
class SpeakerExperiencesAdmin(admin.ModelAdmin):
    """Speaker experience admin."""

    list_display = ("event_name", "description")
    search_fields = ("event_name",)
    list_filter = ("event_name",)
    ordering = ("event_name",)


@admin.register(SpeakerSocialLinks)
class SpeakerSocialLinksAdmin(admin.ModelAdmin):
    """Speaker social links admin."""

    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)
    ordering = ("name",)


@admin.register(OrganizationCFP)
class OrganizationCfpAdmin(admin.ModelAdmin):
    """Organization cfp admin."""

    list_display = ("organization_cfp__name", "description")
    search_fields = ("organization_cfp__name",)
    list_filter = ("organization_cfp__name",)
    ordering = ("organization_cfp__name",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin."""

    list_display = ("user__username",)
    search_fields = ("user__username",)
    list_filter = ("user__username",)
    ordering = ("user__username",)


@admin.register(SpeakerFollow)
class SpeakerFollowAdmin(admin.ModelAdmin):
    """Speaker follow admin."""

    list_display = ("follower__username", "speaker__user_account__username")
    search_fields = ("follow_name__username", "speaker__user_account__username")
    list_filter = ("follower__username", "speaker__user_account__username")
    ordering = ("speaker__user_account__username",)
