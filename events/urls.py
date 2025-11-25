"""events urls."""

from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    path("events/", views.EventListView.as_view(), name="event-list-create"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event-detail"),
]
