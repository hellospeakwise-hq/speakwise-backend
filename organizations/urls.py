"""Organization URLs."""

from django.urls import path

from .views import (
    OrganizationAddOrganizerView,
    OrganizationDetailView,
    OrganizationListCreateView,
    OrganizationMembersView,
    OrganizationRemoveMemberView,
    public_organizations_view,
)

app_name = "organizations"

urlpatterns = [
    # Organization CRUD
    path(
        "organizations/", OrganizationListCreateView.as_view(), name="organization-list"
    ),
    path(
        "organizations/<int:pk>/",
        OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
    # Organization members management
    path(
        "organizations/<int:id>/add-organizer/",
        OrganizationAddOrganizerView.as_view(),
        name="organization-add-organizer",
    ),
    path(
        "organizations/<int:id>/members/",
        OrganizationMembersView.as_view(),
        name="organization-members",
    ),
    path(
        "organizations/<int:id>/members/<int:user_id>/",
        OrganizationRemoveMemberView.as_view(),
        name="organization-remove-member",
    ),
    # Public endpoints
    path(
        "organizations/public/", public_organizations_view, name="public-organizations"
    ),
]
