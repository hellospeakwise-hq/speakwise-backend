"""Custom middleware for request ID correlation and structured logging."""

import logging
import uuid

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """Add a unique request ID to every request for log correlation."""

    def __init__(self, get_response):
        """Initialize the middleware with the given get_response callable."""
        self.get_response = get_response

    def __call__(self, request):
        """Add a unique request ID to the request and set it in the response."""
        request.request_id = str(uuid.uuid4())
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response


class HealthCheckMiddleware:
    """Middleware that intercepts /api/health/ at the middleware level."""

    def __init__(self, get_response):
        """Initialize the middleware with the given get_response callable."""
        self.get_response = get_response

    def __call__(self, request):
        """Intercept the request and handle health check requests."""
        if request.path == "/api/health/":
            try:
                connections["default"].cursor().execute("SELECT 1")
            except OperationalError as e:
                logger.error("Health check failed: DB unavailable: %s", e)
                return JsonResponse(
                    {"status": "error", "detail": "database unavailable"},
                    status=503,
                )
            try:
                from django.core.cache import cache

                cache.set("health_check_ping", "ok", 5)
                if cache.get("health_check_ping") != "ok":
                    raise RuntimeError("Cache set/get mismatch")
            except Exception as e:
                logger.warning("Health check: cache degraded: %s", e)

            return JsonResponse({"status": "ok"}, status=200)
        return self.get_response(request)
