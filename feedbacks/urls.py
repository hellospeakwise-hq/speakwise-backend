"""Urls for feedbacks."""

from django.urls import path

from feedbacks import views

app_name = "feedbacks"

urlpatterns = [
    path(
        "feedbacks/",
        views.FeedbackListView.as_view(),
        name="feedback_list",
    ),
    path(
        "feedbacks/rate/<str:feedback_slug>/",
        views.FeedbackRateView.as_view(),
        name="feedback_rate",
    ),
    path(
        "feedbacks/qrcode/<str:feedback_slug>/",
        views.FeedbackQRCodeView.as_view(),
        name="feedback_qrcode",
    ),
]
