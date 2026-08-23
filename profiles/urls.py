"""speakers urls."""

from django.urls import path

from profiles.views import speaker_views

app_name = "profiles"

urlpatterns = [
    # Speaker profile collection
    path(
        "speakers/",
        speaker_views.SpeakerProfileListCreateView.as_view(),
        name="speakers_list_create",
    ),
    # Experiences (private, per-authenticated user)
    path(
        "speakers/experiences/",
        speaker_views.SpeakerExperiencesListCreateView.as_view(),
        name="speakers_experiences_list_create",
    ),
    path(
        "speakers/experiences/<uuid:pk>/",
        speaker_views.SpeakerExperiencesRetrieveUpdateDestroyView.as_view(),
        name="speakers_experiences_retrieve_update_delete",
    ),
    # Skill tags (must be declared BEFORE generic slug route)
    path(
        "speakers/skills/",
        speaker_views.SpeakerSkillTagsListView.as_view(),
        name="skills_list",
    ),
    path(
        "speakers/skills/<uuid:pk>/",
        speaker_views.SpeakerSkillTagsDetailView.as_view(),
        name="skills_detail",
    ),
    # Speaker deck management
    path(
        "speakers/decks/",
        speaker_views.SpeakerDeckListCreateView.as_view(),
        name="speaker_decks_list_create",
    ),
    path(
        "speakers/decks/<uuid:pk>/",
        speaker_views.SpeakerDeckRetrieveUpdateDestroyView.as_view(),
        name="speaker_deck_detail",
    ),
    # Notifications
    path(
        "notifications/",
        speaker_views.NotificationListView.as_view(),
        name="notification_list",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        speaker_views.NotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    # Public experiences by speaker slug
    path(
        "speakers/<slug:slug>/experiences/",
        speaker_views.PublicSpeakerExperiencesListView.as_view(),
        name="public_speaker_experiences",
    ),
    # Follow / unfollow a speaker (requires auth) + check follow status
    path(
        "speakers/<slug:slug>/follow/",
        speaker_views.SpeakerFollowView.as_view(),
        name="speaker_follow",
    ),
    # List all followers for a speaker (public)
    path(
        "speakers/<slug:slug>/followers/",
        speaker_views.SpeakerFollowersListView.as_view(),
        name="speaker_followers_list",
    ),
    # List all speakers that a speaker follows (public)
    path(
        "speakers/<slug:slug>/following/",
        speaker_views.SpeakerFollowingListView.as_view(),
        name="speaker_following_list",
    ),
    # Single speaker profile by slug (keep last)
    path(
        "speakers/<slug:slug>/",
        speaker_views.SpeakerProfileRetrieveUpdateDestroyView.as_view(),
        name="speakers_retrieve_update_delete",
    ),
]
