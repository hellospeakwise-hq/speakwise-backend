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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/", include("speakers.urls", namespace="speakers")),
    path("api/", include("organizers.urls", namespace="organizers")),
    path("api/", include("organizations.urls", namespace="organizations")),
    path("api/", include("attendees.urls", namespace="attendees")),
    path("api/", include("talks.urls", namespace="talks")),
    path("api/", include("users.urls", namespace="users")),
    path("api/", include("teams.urls", namespace="teams")),
    path("api/", include("events.urls", namespace="events")),
    path("api/", include("feedbacks.urls", namespace="feedbacks")),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
