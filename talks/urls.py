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
    path(
        "talks/review/",
        views.TalkReviewListView.as_view(),
        name="talk-review-list",
    ),
    path(
        "talks/review/<str:slug>/",
        views.TalkReviewDetailView.as_view(),
        name="talk-review-detail",
    ),
    path(
        "talks/review/<str:slug>/delete/",
        views.TalkReviewDeleteView.as_view(),
        name="talk-review-delete",
    ),
]
