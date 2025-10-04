"""Events filters."""

from django_filters import rest_framework as filters

from events.models import Event


class EventFilter(filters.FilterSet):
    """Event filter."""

    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    organization = filters.CharFilter(method="organization_filter")
    country = filters.CharFilter(method="country_filter")
    venue = filters.CharFilter(method="venue_filter")

    def organization_filter(self, queryset, name, value):
        """Filter events by organization name (legacy support)."""
        if value:
            return queryset.filter(organization__name__icontains=value)
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
        fields = ["title", "organization", "country", "venue"]
