"""Admin configuration for the feedback app."""

from django.contrib import admin

from feedbacks.models import EventFeedbackPreference, Feedback

admin.site.register(Feedback)
admin.site.register(EventFeedbackPreference)
