"""speakers admin."""

from django.contrib import admin

from speakers.models import (
    SpeakerExperiences,
    SpeakerProfile,
    SpeakerSkillTag,
    SpeakerSocialLinks,
)

admin.site.register(SpeakerProfile)
admin.site.register(SpeakerSocialLinks)
admin.site.register(SpeakerSkillTag)
admin.site.register(SpeakerExperiences)

# Register your models here.
