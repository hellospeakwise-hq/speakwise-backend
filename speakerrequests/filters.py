"""speaker request filters."""

from django_filters import rest_framework as filters

from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest


class SpeakerRequestFilter(filters.FilterSet):
    """speaker request filter."""

    status = filters.CharFilter(field_name="status", lookup_expr="exact")
    event = filters.NumberFilter(field_name="event__id", lookup_expr="exact")

    class Meta:
        """meta options."""

        model = SpeakerRequest
        fields = ["status", "event"]


class EmailRequestsFilter(filters.FilterSet):
    """Email request filter."""

    request_from = filters.NumberFilter(
        field_name="request_from__id", lookup_expr="exact"
    )
    request_to = filters.NumberFilter(field_name="request_to__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event", lookup_expr="exact")

    class Meta:
        """meta options."""

        model = SpeakerEmailRequests
        fields = ["request_from", "request_to", "event"]
