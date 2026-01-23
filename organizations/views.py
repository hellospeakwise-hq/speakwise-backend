"""Organizations app views."""

from django_filters import rest_framework as filters
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from base.permissions import IsOrganizationMember
from organizations.filters import OrganizationMembershipFilter
from organizations.models import Organization, OrganizationMembership
from organizations.serializers import (
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)


class OrganizationListCreateView(ListCreateAPIView):
    """View for creating and listing organizations."""

    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all().select_related("created_by")
    serializer_class = OrganizationSerializer


class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting an organization."""

    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all().select_related("created_by")
    serializer_class = OrganizationSerializer


class OrganizationMembersView(ListAPIView):
    """View for listing members of an organization."""

    permission_classes = [IsOrganizationMember]
    serializer_class = OrganizationMembershipSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OrganizationMembershipFilter

    def get_queryset(self):
        """Get members of an organization."""
        return OrganizationMembership.objects.filter(
            organization_id=self.kwargs["pk"]
        ).select_related("user", "organization", "added_by")
