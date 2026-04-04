"""speaker request urls."""

from django.urls import path

from speakerrequests import views

app_name = "speakerrequests"

urlpatterns = [
    # Organizer URLs
    path(
        "speaker-requests/",
        views.OrganizerSpeakerRequestListCreateAPIView.as_view(),
        name="speaker-request-list-create",
    ),
    path(
<<<<<<< HEAD
        "speaker-requests/<int:pk>/",
        views.OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView.as_view(),
        name="speaker-request-detail",
=======
        "speaker-requests/<uuid:pk>/",
        views.SPeakerRequestDetailView.as_view(),
        name="speaker_request_retrieve_update_delete",
    ),
    path(
        "speaker-requests/incoming/",
        views.SpeakerRequestsListView.as_view(),
        name="speaker_requests_list",
>>>>>>> 63914ee (update urls)
    ),
    # Speaker URLs
    path(
<<<<<<< HEAD
        "speaker-requests/<int:pk>/respond/",
        views.SpeakerRequestRespondAPIView.as_view(),
        name="speaker-request-respond",
=======
        "speaker-requests/<uuid:pk>/respond/",
        views.SpeakerRequestAcceptView.as_view(),
        name="speaker_request_respond",
>>>>>>> 63914ee (update urls)
    ),
    # Email Request URLs
    path(
        "speaker-requests/email-requests/",
        views.SpeakerEmailRequestListCreateAPIView.as_view(),
        name="speaker-email-request-list-create",
    ),
    path(
        "speaker-requests/email-request/<id>/respond/",
        views.SpeakerEmailRequestRespondAPIView.as_view(),
        name="speaker-email-request-respond",
    ),
]
