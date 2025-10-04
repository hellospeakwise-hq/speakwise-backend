"""Organization views using DRF generic views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.permissions import IsOrganizationAdminPermission
from users.models import User

from .models import Organization, OrganizationMembership, OrganizationRole
from .serializers import (
    AddOrganizerSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)


class OrganizationListCreateView(ListCreateAPIView):
    """List organizations where user is a member and create new organizations."""

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdminPermission]

    def get_queryset(self):
        """Return organizations where user is a member."""
        user = self.request.user
        return (
            Organization.objects.filter(
                organization_memberships__user=user,
                organization_memberships__is_active=True,
            )
            .distinct()
            .order_by("-created_at")
        )

    @extend_schema(description="Create a new organization")
    def create(self, request, *args, **kwargs):
        """Create a new organization."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if organization name is globally unique
        org_name = serializer.validated_data["name"]
        if Organization.objects.filter(name__iexact=org_name).exists():
            return Response(
                {
                    "detail": f"An organization with the name '{org_name}' already exists. Please choose a different name.",
                    "field": "name",
                    "code": "unique_constraint",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the organization
        try:
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            # Handle any database constraint violations
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                return Response(
                    {
                        "detail": "Organization name or email already exists.",
                        "code": "unique_constraint",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise e


class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an organization."""

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdminPermission]
    queryset = Organization.objects.all()

    @extend_schema(description="Get organization details")
    def get(self, request):
        """Retrieve organization details."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Add additional context for members
        data = serializer.data
        data["user_role"] = self._get_user_role_in_organization(request.user, instance)
        data["user_permissions"] = self._get_user_permissions_in_organization(
            request.user, instance
        )

        return Response(data)

    @extend_schema(description="Update organization (admin only)")
    def update(self, request, *args, **kwargs):
        """Update organization (full update)."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Ensure user is admin
        if not instance.is_admin(request.user):
            return Response(
                {"detail": "Only organization admins can update organization details."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Prevent changing created_by
        if "created_by" in serializer.validated_data:
            return Response(
                {"detail": "Cannot change organization creator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check name uniqueness if name is being updated
        if "name" in serializer.validated_data:
            new_name = serializer.validated_data["name"]
            # Check if another organization (not this one) has the same name
            if (
                Organization.objects.filter(name__iexact=new_name)
                .exclude(id=instance.id)
                .exists()
            ):
                return Response(
                    {
                        "detail": f"An organization with the name '{new_name}' already exists. Please choose a different name.",
                        "field": "name",
                        "code": "unique_constraint",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            # Handle any database constraint violations
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                return Response(
                    {
                        "detail": "Organization name or email already exists.",
                        "code": "unique_constraint",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise e

    @extend_schema(description="Delete organization (admin only)")
    def destroy(self, request, *args, **kwargs):
        """Delete organization."""
        instance = self.get_object()

        # Ensure user is admin
        if not instance.is_admin(request.user):
            return Response(
                {"detail": "Only organization admins can delete the organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if organization has events
        if hasattr(instance, "events") and instance.events.exists():
            return Response(
                {
                    "detail": "Cannot delete organization with existing events. "
                    "Please delete or transfer events first.",
                    "events_count": instance.events.count(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Soft delete - mark as inactive instead of hard delete
        instance.is_active = False
        instance.save()

        # Deactivate all memberships
        instance.organization_memberships.update(is_active=False)

        return Response(
            {"detail": "Organization successfully deactivated."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def _get_user_role_in_organization(self, user, organization):
        """Get user's role in the organization."""
        try:
            membership = organization.organization_memberships.get(
                user=user, is_active=True
            )
            return membership.role
        except OrganizationMembership.DoesNotExist:
            return None

    def _get_user_permissions_in_organization(self, user, organization):
        """Get user's permissions in the organization."""
        try:
            membership = organization.organization_memberships.get(
                user=user, is_active=True
            )
            return {
                "can_review_talks": membership.can_review_talks,
                "can_manage_events": membership.can_manage_events,
                "can_add_organizers": membership.can_add_organizers,
                "is_admin": membership.role == OrganizationRole.ADMIN,
            }
        except OrganizationMembership.DoesNotExist:
            return {
                "can_review_talks": False,
                "can_manage_events": False,
                "can_add_organizers": False,
                "is_admin": False,
            }


class OrganizationAddOrganizerView(APIView):
    """Add a user as an organizer to the organization."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddOrganizerSerializer,
        responses={201: OrganizationMembershipSerializer},
        description="Add a user as an organizer to the organization",
    )
    def post(self, request, id):
        """Add a user as an organizer to the organization."""
        try:
            organization = Organization.objects.get(id=id)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is admin
        if not organization.is_admin(request.user):
            return Response(
                {"detail": "Only admins can add organizers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AddOrganizerSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data["user_id"]
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
                )

            # Check if user is already a member
            if organization.is_member(user):
                return Response(
                    {"detail": "User is already a member of this organization."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create membership
            membership = OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=serializer.validated_data["role"],
                added_by=request.user,
                can_review_talks=serializer.validated_data["can_review_talks"],
                can_manage_events=serializer.validated_data["can_manage_events"],
                can_add_organizers=serializer.validated_data["can_add_organizers"],
            )

            response_serializer = OrganizationMembershipSerializer(membership)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationMembersView(APIView):
    """List all members of the organization."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OrganizationMembershipSerializer(many=True)},
        description="List all members of the organization",
    )
    def get(self, request, id):
        """List all members of the organization."""
        try:
            organization = Organization.objects.get(id=id)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is a member
        if not organization.is_member(request.user):
            return Response(
                {"detail": "You must be a member to view organization members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        memberships = organization.organization_memberships.filter(is_active=True)
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class OrganizationRemoveMemberView(APIView):
    """Remove a member from the organization."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={204: None}, description="Remove a member from the organization"
    )
    def delete(self, request, id, user_id):
        """Remove a member from the organization."""
        try:
            organization = Organization.objects.get(id=id)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is admin
        if not organization.is_admin(request.user):
            return Response(
                {"detail": "Only admins can remove members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            user_to_remove = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            membership = organization.organization_memberships.get(
                user=user_to_remove, is_active=True
            )
        except OrganizationMembership.DoesNotExist:
            return Response(
                {"detail": "User is not a member of this organization."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent removing the creator
        if organization.created_by == user_to_remove:
            return Response(
                {"detail": "Cannot remove the organization creator."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deactivate membership
        membership.is_active = False
        membership.save()

        return Response(
            {"detail": "Member successfully removed."},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(
    responses={200: OrganizationSerializer(many=True)},
    description="List all public organizations",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_organizations_view(request):
    """List all public organizations."""
    organizations = Organization.objects.filter(is_active=True).order_by("-created_at")
    serializer = OrganizationSerializer(organizations, many=True)
    return Response(serializer.data)
