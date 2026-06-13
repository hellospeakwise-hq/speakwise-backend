"""team views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from teams.models import TeamMember
from teams.serializers import TeamMemberSerializer


class TeamMemberListView(APIView):
    """View to list all active team members for frontend display."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="List Team Members",
        description="Retrieve a list of all active team members with their social links for frontend display.",
        responses={200: TeamMemberSerializer(many=True)},
    )
    def get(self, request):
        """Handle GET requests to retrieve team members."""
        members = TeamMember.objects.prefetch_related("social_links").filter(
            is_active=True
        )
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
