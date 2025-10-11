"""URL configurations for the organizations app."""

from django.urls import path

from organizations import views

app_name = "organizations"

urlpatterns = [
    path(
        "organizations/",
        views.ListCreateOrganizationView.as_view(),
        name="organization-list-create",
    ),
    path(
        "organizations/<int:pk>/",
        views.OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
    path(
        "organizations/add-organizer/",
        views.AddOrganizerView.as_view(),
        name="add-organizer",
    ),
    path(
        "organizations/<int:pk>/members/",
        views.ListOrganizationMembersView.as_view(),
        name="list-organization-members",
    ),
]
