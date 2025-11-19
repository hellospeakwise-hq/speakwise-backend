"""organization filters module."""

from django_filters import rest_framework as filters

from organizations.models import OrganizationMembership


class OrganizationMembershipFilter(filters.FilterSet):
    """Filter for OrganizationMembership model."""

    user = filters.CharFilter(field_name="user__username", lookup_expr="iexact")
    role = filters.CharFilter(field_name="role", lookup_expr="iexact")
    status = filters.BooleanFilter(field_name="status", lookup_expr="exact")

    class Meta:
        """meta options."""

        model = OrganizationMembership
        fields = ["user", "role", "status"]
