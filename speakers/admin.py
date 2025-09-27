"""speakers admin."""

from django.contrib import admin

from speakers.models import SpeakerProfile, SpeakerSkillTag, SpeakerSocialLinks

admin.site.register(SpeakerProfile)
admin.site.register(SpeakerSocialLinks)
admin.site.register(SpeakerSkillTag)

# Register your models here.
