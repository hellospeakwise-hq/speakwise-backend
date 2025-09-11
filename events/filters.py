"""Events filters."""

from django_filters import rest_framework as filters

from events.models import Event


class EventFilter(filters.FilterSet):
    """Event filter."""

    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    organizer = filters.CharFilter(method="organizer_filter")
    country = filters.CharFilter(method="country_filter")
    venue = filters.CharFilter(method="venue_filter")

    def organizer_filter(self, queryset, name, value):
        """Filter events by organizer name."""
        if value:
            return queryset.filter(organizer__user_account__username__icontains=value)
        return queryset

    def country_filter(self, queryset, name, value):
        """Filter events by country name."""
        if value:
            return queryset.filter(location__country__name__icontains=value)
        return queryset

    def venue_filter(self, queryset, name, value):
        """Filter events by venue name."""
        if value:
            return queryset.filter(location__venue__icontains=value)
        return queryset

    class Meta:
        """Event filter meta options."""

        model = Event
        fields = ["title", "organizer", "country", "venue"]