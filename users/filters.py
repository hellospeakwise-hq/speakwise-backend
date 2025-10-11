"""User filters Module."""

from django.db import models
from django_filters import rest_framework as filters

from users.models import User


class UserFilter(filters.FilterSet):
    """User filter."""

    username = filters.CharFilter(field_name="username", lookup_expr="icontains")
    email = filters.CharFilter(field_name="email", lookup_expr="icontains")

    class Meta:
        """User filter meta options."""

        model = User
        fields = ["username", "email"]

    def filter_users(self, queryset, name, value):
        """Filter users by username or email."""
        if value:
            return queryset.filter(
                models.Q(username__icontains=value) | models.Q(email__icontains=value)
            )
        return queryset
