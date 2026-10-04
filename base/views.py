"""Shared base views."""

from django.db import OperationalError, connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Liveness and Postgres readiness probe for Railway health checks."""

    permission_classes = [AllowAny]

    @extend_schema(tags=["Health"], responses={200: {"type": "object"}})
    def get(self, request, *args, **kwargs):
        """Return ok when the API is up; database reflects Postgres reachability."""
        try:
            connection.ensure_connection()
            database = "ok"
        except OperationalError:
            database = "unavailable"
        payload = {"status": "ok", "database": database}
        http_status = (
            status.HTTP_200_OK
            if database == "ok"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(payload, status=http_status)
