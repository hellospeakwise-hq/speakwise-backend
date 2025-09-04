"""events urls."""

from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    # Events
    path("events/list/", views.EventListAPIView.as_view(), name="event-list"),
    path("events/create/", views.EventCreateAPIView.as_view(), name="event-create"),
    path(
        "events/<int:pk>/",
        views.EventRetrieveUpdateDestroyAPIView.as_view(),
        name="event-retrieve-update-destroy",
    ),
    # Sessions
    path(
        "events/sessions/",
        views.SessionListCreateAPIView.as_view(),
        name="session-list-create",
    ),
    path(
        "events/sessions/<int:pk>/",
        views.SessionRetrieveUpdateDestroyAPIView.as_view(),
        name="session-retrieve-update-destroy",
    ),
    # Event detail with guest speakers (extended serializer)
    path(
        "events/detail/<int:pk>/",
        views.EventDetailAPIView.as_view(),
        name="event-detail-extended",
    ),
]
