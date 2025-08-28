"""talks urls."""

from django.urls import path
from talks import views

app_name = "talks"

urlpatterns = [
    path("talks/", views.TalkListCreateView.as_view(), name="talk-list"),
    path(
        "talks/<int:pk>/",
        views.TalkRetrieveUpdateDestroyView.as_view(),
        name="talk-detail",
    ),
]
