"""speaker request admin."""

from django.contrib import admin

from speakerrequests.models import SpeakerRequest

admin.site.register(SpeakerRequest)
