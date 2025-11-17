"""URL configurations for the organizations app."""

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
        "organizations/<int:pk>/",
        views.OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
]
