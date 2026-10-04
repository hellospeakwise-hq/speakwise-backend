"""Shared base serializers."""

from rest_framework.serializers import CharField, Serializer


class HealthCheckSerializer(Serializer):
    """Read shape for GET /api/health/."""

    status = CharField(read_only=True)
    database = CharField(read_only=True)
