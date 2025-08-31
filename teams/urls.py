"""Team URLs for the SpeakWise application."""

from django.urls import path

from teams.views import TeamMemberListView


app_name = "teams"

urlpatterns = [
    path("teams/", TeamMemberListView.as_view(), name="team-list"),
]