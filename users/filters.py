"""users filters module."""

from django_filters import rest_framework as filters

from users.models import User


class UserFilter(filters.FilterSet):
    """user filter set."""

    email = filters.CharFilter(field_name="email", lookup_expr="icontains")
    username = filters.CharFilter(field_name="username", lookup_expr="icontains")

    class Meta:
        """meta options."""

        model = User
        fields = ["email", "username"]
