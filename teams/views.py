"""team views."""

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from teams.models import TeamMember
from teams.serializers import TeamMemberSerializer


class TeamMemberListView(generics.ListAPIView):
    """View to list all active team members for frontend display."""

    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get queryset with optimizations for better performance."""
        return TeamMember.objects.prefetch_related("social_links").filter(
            is_active=True
        )

    @extend_schema(
        summary="List Team Members",
        description="Retrieve a list of all active team members with their social links for frontend display.",
        responses={200: TeamMemberSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        """Handle GET requests to retrieve team members."""
        return super().get(request, *args, **kwargs)
