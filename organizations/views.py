"""Organizations app views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from organizations.models import Organization, OrganizationMembership
from organizations.permissions import IsOrganizationAdminPermission
from organizations.serializers import (
    AddMemberSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)


# Create your views here.
@extend_schema(
    request=OrganizationSerializer,
    responses=OrganizationSerializer(many=True),
    tags=["Organization"],
)
class ListCreateOrganizationView(ListCreateAPIView):
    """View to list and create organizations."""

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    request=OrganizationSerializer,
    responses=OrganizationSerializer,
    tags=["Organization"],
)
class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, or delete an organization."""

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    request=AddMemberSerializer,
    responses=AddMemberSerializer,
    tags=["Organization"],
)
class AddOrganizerView(CreateAPIView):
    """View to add an organizer to an organization."""

    queryset = OrganizationMembership.objects.all()
    serializer_class = AddMemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdminPermission]

    def perform_create(self, serializer):
        """Set the added_by field to the current user."""
        serializer.save(added_by=self.request.user)


@extend_schema(
    request=OrganizationMembershipSerializer,
    responses=OrganizationMembershipSerializer(many=True),
    tags=["Organization"],
)
class ListOrganizationMembersView(ListAPIView):
    """View to list members of an organization."""

    serializer_class = OrganizationMembershipSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdminPermission]

    def get_queryset(self):
        """Return members of the specified organization."""
        organization_id = self.kwargs.get("pk")
        organization = Organization.objects.get(id=organization_id)
        return organization.get_organizers()
