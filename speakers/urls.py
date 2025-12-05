"""speakers urls."""

from django.urls import path

from speakers import views

app_name = "speakers"

urlpatterns = [
    path(
        "speakers/",
        views.SpeakerProfileListCreateView.as_view(),
        name="speakers_list_create",
    ),
    path(
        "speakers/experiences/",
        views.SpeakerExperiencesListCreateView.as_view(),
        name="speakers_experiences_list_create",
    ),
    path(
        "speakers/experiences/<pk>/",
        views.SpeakerExperiencesRetrieveUpdateDestroyView.as_view(),
        name="speakers_experiences_retrieve_update_delete",
    ),
    path(
        "speakers/<pk>/",
        views.SpeakerProfileRetrieveUpdateDestroyView.as_view(),
        name="speakers_retrieve_update_delete",
    ),
    
]
