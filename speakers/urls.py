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
        "speakers/<int:pk>/",
        views.SpeakerProfileRetrieveUpdateDestroyView.as_view(),
        name="speakers_retrieve_update_delete",
    ),
    path(
        "speakers/<int:pk>/experiences/",
        views.PublicSpeakerExperiencesListView.as_view(),
        name="public_speaker_experiences",
    ),
    path(
        "speakers/<int:pk>/skill-tags/",
        views.SpeakerSkillTagListView.as_view(),
        name="speaker_skill_tags_list",
    ),
    path(
        "speakers/skill-tags/<int:pk>/",
        views.SpeakerSkillTagDetailView.as_view(),
        name="speaker_skill_tag_detail",
    ),
]
