"""organizers urls."""

from django.urls import path
from organizers import views

app_name = "organizers"

urlpatterns = [
    path(
        "organizers/",
        views.OrganizerProfileListCreateView.as_view(),
        name="organizers_list_create",
    ),
    path(
        "organizers/<int:pk>/",
        views.OrganizerProfileRetrieveUpdateDestroyView.as_view(),
        name="organizers_retrieve_update_delete",
    ),
    path(
        "organizers/<int:organizer_id>/social-links/",
        views.OrganizerSocialLinksListCreateView.as_view(),
        name="organizer_social_links_list_create",
    ),
    path(
        "organizers/<int:organizer_id>/social-links/<int:pk>/",
        views.OrganizerSocialLinksRetrieveUpdateDestroyView.as_view(),
        name="organizer_social_links_retrieve_update_delete",
    ),
]
