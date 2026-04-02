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
        "speaker-requests/<int:pk>/",
        views.OrganizerSpeakerRequestRetrieveUpdateDeleteAPIView.as_view(),
        name="speaker-request-detail",
    ),
    # Speaker URLs
    path(
        "speaker-requests/respond/",
        views.SpeakerRequestRespondAPIView.as_view(),
        name="speaker-request-respond",
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
