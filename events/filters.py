"""Events filters."""

from django_filters import rest_framework as filters

from events.models import Event


class EventFilter(filters.FilterSet):
    """Broad public filter for the event catalog."""

    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    event_nickname = filters.CharFilter(
        field_name="event_nickname", lookup_expr="icontains"
    )
    country = filters.CharFilter(field_name="country", lookup_expr="icontains")
    location = filters.CharFilter(field_name="location", lookup_expr="icontains")
    slug = filters.CharFilter(field_name="slug", lookup_expr="icontains")
    submitted_by = filters.CharFilter(
        field_name="submitted_by__username", lookup_expr="icontains"
    )
    is_active = filters.BooleanFilter()
    cfp_open = filters.BooleanFilter()
    cfp_open_date = filters.DateTimeFilter(field_name="cfp_open_date")
    cfp_deadline = filters.DateTimeFilter(field_name="cfp_deadline")
    start_date_time = filters.DateTimeFilter(field_name="start_date_time")
    end_date_time = filters.DateTimeFilter(field_name="end_date_time")

    class Meta:
        """Event filter meta options."""

        model = Event
        fields = [
            "title",
            "event_nickname",
            "country",
            "location",
            "slug",
            "submitted_by",
            "is_active",
            "cfp_open",
            "cfp_open_date",
            "cfp_deadline",
            "start_date_time",
            "end_date_time",
        ]
