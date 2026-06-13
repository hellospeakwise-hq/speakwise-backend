"""project urls."""

import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

logger = logging.getLogger(__name__)


def health_check(request):
    """Health check endpoint for load balancers and orchestrators."""
    try:
        connections["default"].cursor().execute("SELECT 1")
    except OperationalError as e:
        logger.error("Health check failed: DB unavailable: %s", e)
        return JsonResponse(
            {"status": "error", "detail": "database unavailable"}, status=503
        )

    try:
        from django.core.cache import cache

        cache.set("health_check_ping", "ok", 5)
        if cache.get("health_check_ping") != "ok":
            raise RuntimeError("Cache set/get mismatch")
    except Exception as e:
        logger.warning("Health check: cache degraded: %s", e)

    return JsonResponse({"status": "ok"}, status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/", include("speakers.urls", namespace="speakers")),
    path("api/", include("attendees.urls", namespace="attendees")),
    path("api/", include("talks.urls", namespace="talks")),
    path("api/", include("users.urls", namespace="users")),
    path("api/", include("teams.urls", namespace="teams")),
    path("api/", include("events.urls", namespace="events")),
    path("api/", include("feedbacks.urls", namespace="feedbacks")),
    path("api/", include("organizations.urls", namespace="organizations")),
    path("api/", include("speakerrequests.urls", namespace="speakerrequests")),
    path("api/", include("cfps.urls", namespace="cfp")),
    path("api/", include("eventsessions.urls", namespace="sessions")),
    path("api/", include("eventschedules.urls", namespace="eventschedules")),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
