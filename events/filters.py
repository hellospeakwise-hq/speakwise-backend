"""Events filters."""

from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters

from events.models import Event

AFRICAN_COUNTRIES = [
    "ghana", "nigeria", "kenya", "south africa", "egypt", "rwanda", "uganda",
    "angola", "namibia", "ethiopia", "morocco", "senegal", "tanzania", "cameroon",
    "zambia", "zimbabwe", "algeria", "tunisia", "africa",
]

EUROPEAN_COUNTRIES = [
    "united kingdom", "uk", "germany", "france", "portugal", "spain", "italy",
    "netherlands", "poland", "ireland", "sweden", "switzerland", "norway",
    "belgium", "austria", "denmark", "finland", "czechia", "europe",
]

AMERICAN_COUNTRIES = [
    "united states", "usa", "us", "canada", "brazil", "mexico", "argentina",
    "colombia", "chile", "peru", "america",
]

ASIAN_COUNTRIES = [
    "india", "japan", "singapore", "china", "uae", "united arab emirates",
    "south korea", "indonesia", "malaysia", "vietnam", "thailand", "asia",
]


class EventFilter(filters.FilterSet):
    """Broad public filter for the event catalog."""

    search = filters.CharFilter(method="filter_search")
    region = filters.CharFilter(method="filter_region")
    time_period = filters.CharFilter(method="filter_time_period")
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
    is_featured = filters.BooleanFilter()
    is_free = filters.BooleanFilter()
    cfp_open = filters.BooleanFilter()
    cfp_open_date = filters.DateTimeFilter(field_name="cfp_open_date")
    cfp_deadline = filters.DateTimeFilter(field_name="cfp_deadline")
    start_date_time = filters.DateTimeFilter(field_name="start_date_time")
    end_date_time = filters.DateTimeFilter(field_name="end_date_time")

    def filter_search(self, queryset, name, value):
        """Search title, location, country, nickname and description."""
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(title__icontains=val)
            | Q(location__icontains=val)
            | Q(country__icontains=val)
            | Q(event_nickname__icontains=val)
            | Q(description__icontains=val)
        )

    def filter_region(self, queryset, name, value):
        """Filter by continent/region like Africa, Europe, America, Asia."""
        if not value or value.lower() == "all":
            return queryset
        val = value.lower().strip()
        if val == "africa":
            q_list = Q(country__icontains="africa") | Q(location__icontains="africa")
            for c in AFRICAN_COUNTRIES:
                q_list |= Q(country__icontains=c) | Q(location__icontains=c)
            return queryset.filter(q_list)
        elif val == "europe":
            q_list = Q(country__icontains="europe") | Q(location__icontains="europe")
            for c in EUROPEAN_COUNTRIES:
                q_list |= Q(country__icontains=c) | Q(location__icontains=c)
            return queryset.filter(q_list)
        elif val in ["america", "americas"]:
            q_list = Q(country__icontains="america") | Q(location__icontains="america")
            for c in AMERICAN_COUNTRIES:
                q_list |= Q(country__icontains=c) | Q(location__icontains=c)
            return queryset.filter(q_list)
        elif val == "asia":
            q_list = Q(country__icontains="asia") | Q(location__icontains="asia")
            for c in ASIAN_COUNTRIES:
                q_list |= Q(country__icontains=c) | Q(location__icontains=c)
            return queryset.filter(q_list)
        return queryset.filter(Q(country__icontains=val) | Q(location__icontains=val))

    def filter_time_period(self, queryset, name, value):
        """Filter by time period: upcoming, past, this_month."""
        if not value or value.lower() == "all":
            return queryset
        now = timezone.now()
        val = value.lower().strip()
        if val == "upcoming":
            return queryset.filter(start_date_time__gte=now)
        elif val == "past":
            return queryset.filter(end_date_time__lt=now)
        elif val in ["this_month", "month"]:
            return queryset.filter(
                start_date_time__year=now.year,
                start_date_time__month=now.month,
            )
        return queryset

    class Meta:
        """Event filter meta options."""

        model = Event
        fields = [
            "search",
            "region",
            "time_period",
            "title",
            "event_nickname",
            "country",
            "location",
            "slug",
            "submitted_by",
            "is_active",
            "is_featured",
            "is_free",
            "cfp_open",
            "cfp_open_date",
            "cfp_deadline",
            "start_date_time",
            "end_date_time",
        ]
