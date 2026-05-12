"""session urls."""

from django.urls import path

from eventsessions.views import (
    SessionDetailView,
    SessionListCreateView,
    SessionPublicListView,
)

app_name = "eventsessions"

urlpatterns = [
    path(
        "sessions/<uuid:session_id>/",
        SessionDetailView.as_view(),
        name="session-detail",
    ),
    path(
        "sessions/",
        SessionListCreateView.as_view(),
        name="session-list-base",
    ),
    path(
        "sessions/<str:event_slug>/",
        SessionListCreateView.as_view(),
        name="session-list",
    ),
    path(
        "sessions/<str:event_slug>/public/",
        SessionPublicListView.as_view(),
        name="session-public-list",
    ),
]
