"""Organization URL patterns."""

from django.urls import path

from profiles.views import organization_views

app_name = "organizations"

urlpatterns = [
    path(
        "organization/",
        organization_views.OrganizationProfileListCreateView.as_view(),
        name="organization-list-create",
    ),
    path(
        "organization/<uuid:pk>/",
        organization_views.OrganizationProfileDetailView.as_view(),
        name="organization-detail",
    ),
]
