"""speakers admin."""

from django.contrib import admin

from speakers.models import (
    Notification,
    SpeakerDeck,
    SpeakerExperiences,
    SpeakerFollow,
    SpeakerProfile,
    SpeakerSkillTag,
    SpeakerSocialLinks,
)

admin.site.register(SpeakerProfile)
admin.site.register(SpeakerSocialLinks)
admin.site.register(SpeakerSkillTag)
admin.site.register(SpeakerExperiences)
admin.site.register(SpeakerFollow)
admin.site.register(SpeakerDeck)
admin.site.register(Notification)
