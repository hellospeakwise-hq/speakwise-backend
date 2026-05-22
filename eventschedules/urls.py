"""Event schedules URLs."""

from django.urls import path

from .views import EventScheduleListCreateView, EventScheduleRetrieveUpdateDestroyView

app_name = "eventschedules"

urlpatterns = [
    path(
        "eventschedules/<str:event_slug>/",
        EventScheduleListCreateView.as_view(),
        name="event-schedules-create",
    ),
    path(
        "eventschedules/<uuid:schedule_id>/",
        EventScheduleRetrieveUpdateDestroyView.as_view(),
        name="event-schedule-ret",
    ),
]
