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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        "speaker-requests/<int:pk>/",
        views.OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView.as_view(),
        name="speaker-request-detail",
=======
        "speaker-requests/<uuid:pk>/",
        views.SPeakerRequestDetailView.as_view(),
        name="speaker_request_retrieve_update_delete",
=======
        "speaker-requests/<int:pk>/",
        views.OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView.as_view(),
        name="speaker-request-detail",
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
        "speaker-requests/<uuid:pk>/",
        views.SPeakerRequestDetailView.as_view(),
        name="speaker_request_retrieve_update_delete",
>>>>>>> c4b309a (update urls)
    ),
    path(
<<<<<<< HEAD
<<<<<<< HEAD
        "speaker-requests/incoming/",
<<<<<<< HEAD
        views.SpeakerRequestsListView.as_view(),
        name="speaker_requests_list",
>>>>>>> 63914ee (update urls)
=======
        views.SpeakerIncomingRequestListAPIView.as_view(),
        name="speaker-request-incoming-list",
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
    ),
    # Speaker URLs
    path(
<<<<<<< HEAD
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
=======
        "speaker-requests/<int:pk>/respond/",
        views.SpeakerRequestRespondAPIView.as_view(),
        name="speaker-request-respond",
    ),
    
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
        "speaker-requests/respond/",
        views.SpeakerRequestRespondAPIView.as_view(),
        name="speaker-request-respond",
    ),
>>>>>>> 7255978 (refactor speakerrequest API)
    # Email Request URLs
=======
        "speaker-requests/incoming/",
        views.SpeakerRequestsListView.as_view(),
        name="speaker_requests_list",
    ),
    path(
        "speaker-requests/<uuid:pk>/respond/",
        views.SpeakerRequestAcceptView.as_view(),
        name="speaker_request_respond",
    ),
>>>>>>> c4b309a (update urls)
    path(
        "speaker-requests/email-requests/",
        views.SpeakerEmailRequestListView.as_view(),
        name="speaker_email_requests_list_create",
    ),
    path(
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        "speaker-requests/email-request/<id>/respond/",
        views.SpeakerEmailRequestRespondAPIView.as_view(),
        name="speaker-email-request-respond",
=======
        "speaker-requests/email-requests/<uuid:pk>/",
        views.SpeakerEmailRequestRetrieveUpdateAPIView.as_view(),
        name="speaker-email-request-detail",
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
        "speaker-requests/email-request/<id>/respond/",
        views.SpeakerEmailRequestRespondAPIView.as_view(),
        name="speaker-email-request-respond",
>>>>>>> 7255978 (refactor speakerrequest API)
=======
        "speaker-requests/email-requests/<uuid:pk>/",
        views.SpeakerEmailRequestDetailView.as_view(),
        name="speaker_email_request_retrieve_update",
>>>>>>> c4b309a (update urls)
    ),
]
