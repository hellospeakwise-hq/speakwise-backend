"""Organizations app views."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import (
    IsOrganizationAdminOrOrganizer,
    IsOrganizationMember,
)
from organizations.filters import OrganizationMembershipFilter
from organizations.models import Organization, OrganizationMembership
from organizations.serializers import (
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)


class OrganizationListCreateView(APIView):
    """View for creating and listing organizations."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="organizations_list",
        request=OrganizationSerializer,
        responses={201: OrganizationSerializer},
    )
    def get(self, request) -> Response:
        """List all organizations."""
        organizations = Organization.objects.filter(
            organization_memberships__user=request.user,
            organization_memberships__is_active=True,
        ).distinct()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizationSerializer, responses={201: OrganizationSerializer}
    )
    def post(self, request) -> Response:
        """Create a new organization."""
        serializer = OrganizationSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetailView(APIView):
    """View for retrieving, updating, and deleting an organization."""

    def get_permissions(self):
        """Allow get for organization members and patch/delete for admins/organizers."""
        if self.request.method == "GET":
            return [IsOrganizationMember()]
        return [IsOrganizationAdminOrOrganizer()]

    @extend_schema(
        operation_id="organizations_retrieve", responses={200: OrganizationSerializer}
    )
    def get(self, request, slug: str) -> Response:
        """Retrieve an organization."""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizationSerializer, responses={200: OrganizationSerializer}
    )
    def patch(self, request, slug: str) -> Response:
        """Update an organization."""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)

        serializer = OrganizationSerializer(
            organization, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: None})
    def delete(self, request, slug: str) -> Response:
        """Delete an organization."""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationMembershipListCreateView(APIView):
    """View for listing members of an organization."""

    def get_permissions(self):
        """Get for members and post/delete for admins/organizers."""
        if self.request.method == "GET":
            return [IsOrganizationMember()]
        return [IsOrganizationAdminOrOrganizer()]

    @extend_schema(responses={200: OrganizationMembershipSerializer(many=True)})
    def get(self, request, slug: str) -> Response:
        """List members of an organization."""
        organization = get_object_or_404(Organization, slug=str(slug))
        self.check_object_permissions(request, organization)
        organization_members = OrganizationMembership.objects.filter(
            organization=organization
        )
        members_filters = OrganizationMembershipFilter(
            request.GET, queryset=organization_members
        )
        serializer = OrganizationMembershipSerializer(members_filters.qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizationMembershipSerializer,
        responses={201: OrganizationMembershipSerializer},
    )
    def post(self, request, slug: str) -> Response:
        """Add a member to an organization."""
        organization = get_object_or_404(Organization, slug=slug)
        self.check_object_permissions(request, organization)
        serializer = OrganizationMembershipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(organization=organization, added_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationMembershipDeleteView(APIView):
    """community membership delete view."""

    permission_classes = [IsOrganizationAdminOrOrganizer]

    @extend_schema(responses={200: None})
    def delete(self, request, org_slug: str, username: str) -> Response:
        """Remove a member from an organization."""
        organization = get_object_or_404(Organization, slug=org_slug)
        self.check_object_permissions(request, organization)
        try:
            OrganizationMembership.objects.get(
                organization=organization, user__username=username
            ).delete()
        except OrganizationMembership.DoesNotExist:
            return NotFound(detail="Member not found")
        return Response(status=status.HTTP_204_NO_CONTENT)
