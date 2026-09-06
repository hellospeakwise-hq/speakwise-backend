"""Organization views for the profiles app."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, views
from rest_framework.response import Response

from profiles.models.organization_models import OrganizationProfile
from profiles.serializers.organization_serializers import OrganizationProfileSerializer


class OrganizationProfileListCreateView(views.APIView):
    """View to list and create organization profiles."""

    def get_permissions(self):
        """Return view permission based on request."""
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(responses={200: OrganizationProfileSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """List all organization profiles."""
        organizations = OrganizationProfile.objects.all()
        serializer = OrganizationProfileSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizationProfileSerializer,
        responses={201: OrganizationProfileSerializer},
    )
    def post(self, request, *args, **kwargs):
        """Create a new organization profile owned by the requesting user."""
        serializer = OrganizationProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=OrganizationProfileSerializer,
    responses={200: OrganizationProfileSerializer},
)
class OrganizationProfileDetailView(views.APIView):
    """View to retrieve, update, or delete an organization profile."""

    def get_permissions(self):
        """Return permission based on request."""
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, pk, *args, **kwargs):
        """Retrieve an organization profile."""
        organization = get_object_or_404(OrganizationProfile, pk=pk)
        if not organization:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationProfileSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        """Update an organization profile."""
        organization = get_object_or_404(OrganizationProfile, pk=pk)
        if not organization:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationProfileSerializer(organization, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """Delete an organization profile."""
        organization = get_object_or_404(OrganizationProfile, pk=pk)
        if not organization:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
