"""attendees urls."""

from django.urls import path
from attendees import views

app_name = "attendees"

urlpatterns = [
    path(
        "attendees/",
        views.AttendeeListCreateView.as_view(),
        name="attendees-list-create",
    ),
    path(
        "attendees/<pk>/",
        views.AttendeeRetrieveUpdateDestroyView.as_view(),
        name="attendee-detail",
    ),
]
