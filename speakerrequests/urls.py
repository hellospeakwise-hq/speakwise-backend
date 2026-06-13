"""speaker request urls."""

from django.urls import path

from speakerrequests.views import (
    CreateSpeakerRequestView,
    EmailSpeakerRequestView,
    SpeakerRequestByOrganizationView,
    SpeakerRequestByRequestedSpeakerView,
    SpeakerRequestsView,
)

app_name = "speakerrequests"

urlpatterns = [
    path(
        "speaker-requests/",
        CreateSpeakerRequestView.as_view(),
        name="speaker_requests_list_create",
    ),
    path(
        "speaker-requests/<str:speaker_slug>/",
        SpeakerRequestsView.as_view(),
        name="speaker_request_retrieve_update_delete",
    ),
    path(
        "speaker-requests/<str:org_slug>/requests",
        SpeakerRequestByOrganizationView.as_view(),
        name="speaker_requests_list",
    ),
    path(
        "speaker-requests/<str:speaker_slug>/requests/",
        SpeakerRequestByRequestedSpeakerView.as_view(),
        name="speaker_request_respond",
    ),
    path(
        "speaker-requests/email-requests/",
        EmailSpeakerRequestView.as_view(),
        name="speaker_email_requests_list_create",
    ),
]
