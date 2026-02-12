"""speakers urls."""

from django.urls import path

from speakers import views

app_name = "speakers"

urlpatterns = [
    # Speaker profile collection
    path(
        "speakers/",
        views.SpeakerProfileListCreateView.as_view(),
        name="speakers_list_create",
    ),
    # Experiences (private, per-authenticated user)
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
    # Skill tags (must be declared BEFORE generic slug route)
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
    # Public experiences by speaker slug
    path(
        "speakers/<slug:slug>/experiences/",
        views.PublicSpeakerExperiencesListView.as_view(),
        name="public_speaker_experiences",
    ),
    # Single speaker profile by slug (keep last)
    path(
        "speakers/<slug:slug>/",
        views.SpeakerProfileRetrieveUpdateDestroyView.as_view(),
        name="speakers_retrieve_update_delete",
    ),
]
