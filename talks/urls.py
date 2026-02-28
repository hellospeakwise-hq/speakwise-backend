"""talks urls."""

from django.urls import path

from talks import views

app_name = "talks"

urlpatterns = [
    path("talks/", views.TalkListCreateView.as_view(), name="talk-list"),
    path(
        "talks/<int:pk>/",
        views.TalkRetrieveUpdateDestroyView.as_view(),
        name="talk-detail",
    ),
    # Public endpoints
    path(
        "talks/<slug:slug>/reviews/",
        views.TalkReviewSubmitView.as_view(),
        name="talk-review-submit",
    ),
    path(
        "talks/<slug:slug>/",
        views.PublicTalkDetailView.as_view(),
        name="talk-public-detail",
    ),
    path(
        "speakers/<slug:slug>/talks/",
        views.SpeakerPublicTalksView.as_view(),
        name="speaker-public-talks",
    ),
]
