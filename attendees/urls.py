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
    path("attendees/verify/", views.verify_attendee, name="verify-attendee"),
    path(
        "attendees/<int:pk>/",
        views.AttendeeRetrieveUpdateDestroyView.as_view(),
        name="attendee-detail",
    ),
]
