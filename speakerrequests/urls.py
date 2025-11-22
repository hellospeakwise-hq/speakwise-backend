"""speaker request urls."""

from django.urls import path

from speakerrequests import views

app_name = "speakerrequests"

urlpatterns = [
    path(
        "speaker-requests/",
        views.SpeakerRequestListView.as_view(),
        name="speaker_requests_list_create",
    ),
    path(
        "speaker-requests/<int:pk>/",
        views.SPeakerRequestDetailView.as_view(),
        name="speaker_request_retrieve_update_delete",
    ),
    path(
        "speaker-requests/incoming/",
        views.SpeakerRequestsListView.as_view(),
        name="speaker_requests_list",
    ),
    path(
        "speaker-requests/<int:pk>/respond/",
        views.SpeakerRequestAcceptView.as_view(),
        name="speaker_request_respond",
    ),
]
