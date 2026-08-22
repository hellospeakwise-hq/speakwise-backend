"""events urls."""

from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    path("events/tags/", views.TagListView.as_view(), name="tag-list"),
    path("events/", views.EventListView.as_view(), name="event-list-create"),
    path(
        "events/review/", views.EventReviewListView.as_view(), name="event-review-list"
    ),
    path(
        "events/<str:slug>/approve/",
        views.EventApproveView.as_view(),
        name="event-approve",
    ),
    path(
        "events/<str:slug>/toggle-speaker-deck-upload/",
        views.EventSpeakerDeckToggleView.as_view(),
        name="event-toggle-speaker-deck",
    ),
    path("events/<str:slug>/", views.EventDetailView.as_view(), name="event-detail"),
]
