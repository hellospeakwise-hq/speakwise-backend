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
        "speakers/experiences/<int:pk>/",
        views.SpeakerExperiencesRetrieveUpdateDestroyView.as_view(),
        name="speakers_experiences_retrieve_update_delete",
    ),
    path(
        "speakers/<slug:slug>/",
        views.SpeakerProfileRetrieveUpdateDestroyView.as_view(),
        name="speakers_retrieve_update_delete",
    ),
    path(
        "speakers/<slug:slug>/experiences/",
        views.PublicSpeakerExperiencesListView.as_view(),
        name="public_speaker_experiences",
    ),
    path(
        "speakers/skills/",
        views.SpeakerSkillTagsListView.as_view(),
        name="skills_list",
    ),
    path(
        "speakers/skills/<int:pk>/",
        views.SpeakerSkillTagsDetailView.as_view(),
        name="skills_detail",
    ),
]
