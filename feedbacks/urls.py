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
        "feedbacks/toggle/",
        views.SpeakerFeedbackToggleView.as_view(),
        name="feedback_toggle",
    ),
]
