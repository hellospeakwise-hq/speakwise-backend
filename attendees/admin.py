"""attendees admin."""

from django.contrib import admin

from attendees.models import AttendeeProfile, AttendeeSocialLinks

admin.site.register(AttendeeProfile)
admin.site.register(AttendeeSocialLinks)
