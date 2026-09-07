"""events urls."""

from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    path("events/", views.EventListView.as_view(), name="event-list-create"),
    path(
        "events/cfp-market/",
        views.CFPMarketListView.as_view(),
        name="cfp-market",
    ),
    path("events/<str:slug>/", views.EventDetailView.as_view(), name="event-detail"),
    path("events/mine", views.MyEventsListView.as_view(), name="events-mine"),
]
