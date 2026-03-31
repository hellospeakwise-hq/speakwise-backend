"""events urls."""

from django.urls import path

from events import views

app_name = "events"

urlpatterns = [
    path("events/tags/", views.TagListView.as_view(), name="tag-list"),
    path("events/", views.EventListView.as_view(), name="event-list-create"),
    path("events/<str:slug>/", views.EventDetailView.as_view(), name="event-detail"),
]
