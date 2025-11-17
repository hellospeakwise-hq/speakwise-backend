"""Organizations app views."""

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization
from organizations.serializers import OrganizationSerializer


class OrganizationListCreateView(APIView):
    """View for creating and listing organizations."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OrganizationSerializer, responses={201: OrganizationSerializer}
    )
    def get(self, request):
        """List all organizations."""
        organizations = Organization.objects.all()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizationSerializer, responses={201: OrganizationSerializer}
    )
    def post(self, request):
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

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Get an organization by its primary key."""
        try:
            return Organization.objects.get(pk=pk)
        except Organization.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses={200: OrganizationSerializer})
    def get(self, request, pk):
        """Retrieve an organization."""
        organization = self.get_object(pk)
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizationSerializer, responses={200: OrganizationSerializer}
    )
    def patch(self, request, pk):
        """Update an organization."""
        organization = self.get_object(pk)
        serializer = OrganizationSerializer(
            organization, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        """Delete an organization."""
        organization = self.get_object(pk)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
