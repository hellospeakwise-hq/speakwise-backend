"""CFP urls."""

from django.urls import path

from cfps import views

app_name = "cfp"

urlpatterns = [
    path(
        "events/<str:slug>/cfp/",
        views.CFPSubmissionListCreateView.as_view(),
        name="cfp-list-create",
    ),
    path(
        "events/<str:slug>/cfp/review-queue/",
        views.CFPReviewQueueView.as_view(),
        name="cfp-review-queue",
    ),
    path("cfp/mine/", views.MyCFPSubmissionsView.as_view(), name="cfp-mine"),
    path("cfp/<uuid:pk>/", views.CFPSubmissionDetailView.as_view(), name="cfp-detail"),
    path(
        "cfp/<uuid:pk>/status/",
        views.CFPStatusUpdateView.as_view(),
        name="cfp-status-update",
    ),
    path(
        "cfp/<uuid:pk>/review/",
        views.CFPReviewView.as_view(),
        name="cfp-review",
    ),
    path(
        "cfp/<uuid:pk>/reviews/",
        views.CFPReviewListView.as_view(),
        name="cfp-reviews-list",
    ),
]
