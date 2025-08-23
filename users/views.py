"""users views."""

from rest_framework.generics import CreateAPIView
from users.serializers import UserSerializer
from users.models import User
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout


@extend_schema(responses=UserSerializer)
class UserCreateView(CreateAPIView):
    """User create view."""

    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]


class UserLogoutView(APIView):
    """User logout view."""

    def post(self, request):
        """logout user."""
        refresh = request.data.get("refresh")
        if refresh is None:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh)
            token.blacklist()
            logout(request)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
