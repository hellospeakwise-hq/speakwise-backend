"""speakers admin."""

from django.contrib import admin

from profiles.models.speaker_models import (
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
