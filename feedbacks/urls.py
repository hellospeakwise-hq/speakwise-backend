"""Urls for feedbacks."""

from django.urls import path

from feedbacks import views

app_name = "feedbacks"

urlpatterns = [
    path(
        "feedbacks/",
        views.FeedbackListCreateView.as_view(),
        name="feedbacks_list_create",
    ),
    path(
        "feedbacks/preferences/<uuid:event_id>/",
        views.EventFeedbackPreferenceView.as_view(),
        name="event_feedback_preference",
    ),
]
