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
        "speakers/experiences/<uuid:pk>/",
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
        "speakers/skills/<uuid:pk>/",
        views.SpeakerSkillTagsDetailView.as_view(),
        name="skills_detail",
    ),
    # Speaker deck management
    path(
        "speakers/decks/",
        views.SpeakerDeckListCreateView.as_view(),
        name="speaker_decks_list_create",
    ),
    path(
        "speakers/decks/<uuid:pk>/",
        views.SpeakerDeckRetrieveUpdateDestroyView.as_view(),
        name="speaker_deck_detail",
    ),
    # Notifications
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notification_list",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        views.NotificationMarkReadView.as_view(),
        name="notification_mark_read",
    ),
    # Public experiences by speaker slug
    path(
        "speakers/<slug:slug>/experiences/",
        views.PublicSpeakerExperiencesListView.as_view(),
        name="public_speaker_experiences",
    ),
    # Follow / unfollow a speaker (requires auth) + check follow status
    path(
        "speakers/<slug:slug>/follow/",
        views.SpeakerFollowView.as_view(),
        name="speaker_follow",
    ),
    # List all followers for a speaker (public)
    path(
        "speakers/<slug:slug>/followers/",
        views.SpeakerFollowersListView.as_view(),
        name="speaker_followers_list",
    ),
    # List all speakers that a speaker follows (public)
    path(
        "speakers/<slug:slug>/following/",
        views.SpeakerFollowingListView.as_view(),
        name="speaker_following_list",
    ),
    # Single speaker profile by slug (keep last)
    path(
        "speakers/<slug:slug>/",
        views.SpeakerProfileRetrieveUpdateDestroyView.as_view(),
        name="speakers_retrieve_update_delete",
    ),
]
