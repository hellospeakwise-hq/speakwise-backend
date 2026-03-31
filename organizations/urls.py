"""URL configurations for the organization app."""

from django.urls import path

from organizations import views

app_name = "organizations"

urlpatterns = [
    path(
        "organizations/",
        views.OrganizationListCreateView.as_view(),
        name="organization-list-create",
    ),
    path(
        "organizations/<slug:slug>/",
        views.OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
    path(
        "organizations/<slug:slug>/members/",
        views.OrganizationMembershipListCreateView.as_view(),
        name="organization-members-list-create-delete",
    ),
    path(
        "organizations/<slug:org_slug>/members/<str:username>/",
        views.OrganizationMembershipDeleteView.as_view(),
        name="organization-members-delete",
    ),
]
