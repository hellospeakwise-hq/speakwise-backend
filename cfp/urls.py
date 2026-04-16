"""CFP urls."""

from django.urls import path

from cfp import views

app_name = "cfp"

urlpatterns = [
    path(
        "events/<str:slug>/cfp/",
        views.CFPSubmissionListCreateView.as_view(),
        name="cfp-list-create",
    ),
    path("cfp/<uuid:pk>/", views.CFPSubmissionDetailView.as_view(), name="cfp-detail"),
    path(
        "cfp/<uuid:pk>/status/",
        views.CFPStatusUpdateView.as_view(),
        name="cfp-status-update",
    ),
]
