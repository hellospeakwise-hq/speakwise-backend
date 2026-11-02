"""URLs for Web3 Badges & Gamification."""

from django.urls import path

from badges.views import (
    BadgeDefinitionsListView,
    BadgeMetadataView,
    ClaimBadgeView,
    SpeakerBadgesListView,
)

app_name = "badges"

urlpatterns = [
    path(
        "badges/definitions/",
        BadgeDefinitionsListView.as_view(),
        name="definitions-list",
    ),
    path("badges/claim/", ClaimBadgeView.as_view(), name="claim-badge"),
    path(
        "badges/metadata/<str:token_id>/",
        BadgeMetadataView.as_view(),
        name="badge-metadata",
    ),
    path(
        "speakers/<slug:slug>/badges/",
        SpeakerBadgesListView.as_view(),
        name="speaker-badges",
    ),
]
