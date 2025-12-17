"""attendees urls."""

from django.urls import path

from attendees import views

app_name = "attendees"

urlpatterns = [
    # path(
    #     "attendees/",
    #     views.AttendeeListCreateView.as_view(),
    #     name="attendees-list-create",
    # ),
    #
    # path("attendees/verify/", views.verify_attendee, name="verify-attendee"),
    # path(
    #     "attendees/<int:pk>/",
    #     views.AttendeeRetrieveUpdateDestroyView.as_view(),
    #     name="attendee-detail",
    # ),
    path(
        "attendance/",
        views.CreateAttendanceByFileUploadView.as_view(),
        name="upload-attendance-file",
    ),
    path(
        "attendance/upload-attendance/",
        views.upload_attendance_view,
        name="upload-attendance",
    ),
    path(
        "attendance/<int:pk>/",
        views.AttendanceDetailView.as_view(),
        name="attendance-detail",
    ),
]
