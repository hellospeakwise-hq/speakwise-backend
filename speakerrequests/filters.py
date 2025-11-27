"""speaker request filters."""

from django_filters import rest_framework as filters

from speakerrequests.models import SpeakerRequest


class SpeakerRequestFilter(filters.FilterSet):
    """speaker request filter."""

    status = filters.CharFilter(field_name="status", lookup_expr="exact")
    event = filters.NumberFilter(field_name="event__id", lookup_expr="exact")

    class Meta:
        """meta options."""

        model = SpeakerRequest
        fields = ["status", "event"]
