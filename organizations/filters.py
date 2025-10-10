"""Organization Filters Module."""

from django_filters import rest_framework as filters

from organizations.models import Organization


class OrganizationFilter(filters.FilterSet):
    """Organization filter."""

    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    created_by = filters.CharFilter(method="created_by_filter")

    def created_by_filter(self, queryset, name, value):
        """Filter organizations by creator's username."""
        if value:
            return queryset.filter(created_by__username__icontains=value)
        return queryset

    def name_by_filter(self, queryset, name, value):
        """Filter organizations by name."""
        if value:
            return queryset.filter(name__icontains=value)
        return queryset

    class Meta:
        """Organization filter meta options."""

        model = Organization
        fields = ["name", "created_by"]
