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
    ),
    
    # Speaker URLs
    path(
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
    # Email Request URLs
    path(
        "speaker-requests/email-requests/",
        views.SpeakerEmailRequestListCreateAPIView.as_view(),
        name="speaker-email-request-list-create",
    ),
    path(
<<<<<<< HEAD
        "speaker-requests/email-request/<id>/respond/",
        views.SpeakerEmailRequestRespondAPIView.as_view(),
        name="speaker-email-request-respond",
=======
        "speaker-requests/email-requests/<uuid:pk>/",
        views.SpeakerEmailRequestRetrieveUpdateAPIView.as_view(),
        name="speaker-email-request-detail",
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
    ),
]
