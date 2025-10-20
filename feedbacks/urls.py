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
        "feedbacks/<int:pk>/",
        views.FeedbackRetrieveUpdateDestroyView.as_view(),
        name="feedbacks_retrieve_update_delete",
    ),
    path("verify_attendee/", views.verify_attendee, name="verify_attendee"),
]
