"""project urls."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

v1_urlpatterns = [
    path("speakers/", include("speakers.urls", namespace="speakers")),
    path("attendees/", include("attendees.urls", namespace="attendees")),
    path("talks/", include("talks.urls", namespace="talks")),
    path("users/", include("users.urls", namespace="users")),
    path("teams/", include("teams.urls", namespace="teams")),
    path("events/", include("events.urls", namespace="events")),
    path("feedbacks/", include("feedbacks.urls", namespace="feedbacks")),
    path("organizations/", include("organizations.urls", namespace="organizations")),
    path("speakerrequests/", include("speakerrequests.urls", namespace="speakerrequests")),
    # Documentation within v1
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="v1:schema"),
        name="swagger-ui",
    ),
    path("docs/redoc/", SpectacularRedocView.as_view(), name="redoc"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((v1_urlpatterns, "v1"), namespace="v1")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
