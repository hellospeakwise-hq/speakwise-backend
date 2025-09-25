"""Admin configuration for the feedback app."""

from django.contrib import admin

from feedbacks.models import Feedback

admin.site.register(Feedback)
