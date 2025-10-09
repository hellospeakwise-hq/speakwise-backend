"""Organizations app views."""

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from organizations.models import Organization
from organizations.serializers import OrganizationSerializer


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
    responses=OrganizationSerializer(many=True),
    tags=["Organization"],
)
class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, or delete an organization."""

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
