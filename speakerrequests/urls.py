"""speaker request urls."""

from django.urls import path

from speakerrequests import views

app_name = "speakerrequest"

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
        "speaker-requests/speaker/<int:pk>/",
        views.SpeakerRequestsListView.as_view(),
        name="speaker_request_speaker",
    ),
]
