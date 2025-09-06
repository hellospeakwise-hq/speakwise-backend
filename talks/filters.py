"""talks filters."""

from django_filters import rest_framework as filters

from talks.models import Talks


class TalksFilter(filters.FilterSet):
    """talks filter."""

    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    category = filters.CharFilter(field_name="category", lookup_expr="icontains")
    speaker = filters.CharFilter(method="speaker_filter", lookup_expr="icontains")

    def speaker_filter(self, queryset, name, value):
        """Filter talks by speaker name."""
        if value:
            return queryset.filter(speaker__user_account__username=value)
        return queryset

    class Meta:
        """talks filter meta options."""

        model = Talks
        fields = ["title", "category", "speaker"]
