"""users views."""

import logging
from abc import ABC, abstractmethod

from dj_rest_auth.views import LoginView
from django.contrib.auth import logout
from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.filters import UserFilter
from users.models import User
from users.serializers import (
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from users.services import EmailService

logger = logging.getLogger(__name__)


class PasswordResetThrottle(UserRateThrottle):
    """Throttle for password reset requests."""

    scope = "password_reset"


class RegistrationThrottle(UserRateThrottle):
    """Throttle for registration requests."""

    scope = "registration"


@extend_schema(request=UserSerializer, responses=UserSerializer)
class UserCreateView(APIView):
    """User create view."""

    permission_classes = [AllowAny]
    throttle_classes = [RegistrationThrottle]

    def post(self, request):
        """Create a new user."""
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            EmailService.send_welcome_email(user)
        except Exception:
            logger.warning(
                "Welcome email failed for user ID: %s", user.id, exc_info=True
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserLogoutView(APIView):
    """User logout view."""

    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        """Logout user."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data["refresh"]
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


class LoginBaseClass(ABC, LoginView):
    """This class inherits the LoginView from the rest_auth package.
    Django rest auth lib does not support the refresh token
    logic. However,restframework_simplejwt does. Rest auth was
    used because it's based off all-auth which can be used for
    social logins as well as signing in with either username or
    password(of which simplejwt does not support). The two libraries
    were combined to give the required results.
    """

    def get_extra_payload(self) -> dict:
        """This method is used to add extra payload to the refresh token."""
        return {}

    def get_token(self, user):
        """Generate the refresh token."""
        refresh_token = RefreshToken.for_user(user)
        for key, value in self.get_extra_payload().items():
            refresh_token[key] = value
        return refresh_token

    @abstractmethod
    def login(self):
        """Login in the user."""

    def get_response(self):
        """Return the response with the refresh token."""
        data = {}

        refresh = self.get_token(self.user)
        # generate access and refresh tokens
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        data.update(self.get_extra_payload())

        return Response(data)


@extend_schema(request=UserLoginSerializer, responses=UserSerializer)
class UserLoginView(LoginBaseClass):
    """Login view for speaker."""

    def login(self):
        """Login the speaker."""
        self.user = self.serializer.validated_data["user"]
        return self.user

    def get_extra_payload(self) -> dict:
        """Return minimal user data with login response."""
        return {
            "user_id": str(self.user.id),
            "email": self.user.email,
            "username": self.user.username,
        }


@extend_schema(responses=PasswordResetRequestSerializer)
class PasswordResetRequestView(APIView):
    """Password request view for users."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [PasswordResetThrottle]

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        """Request password reset for email."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.context["user"]

        EmailService.send_password_reset_email(user, request)

        return Response(
            {"detail": "Password reset email sent successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema(responses=PasswordResetConfirmSerializer)
class PasswordResetConfirmView(APIView):
    """Password request confirm view."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
    def post(self, request):
        """Confirm password reset."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.context["user"]  # User set in serializer's validate
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(
            {"detail": "Password reset successfully."}, status=status.HTTP_200_OK
        )


class RetrieveUpdateAuthenticatedUserView(APIView):
    """View to retrieve and update the authenticated user's details."""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Get the authenticated user."""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist as err:
            raise Http404 from err

    @extend_schema(responses=UserProfileSerializer)
    def get(self, request):
        """Retrieve the authenticated user's details."""
        user = self.get_object(request.user.pk)
        serializer = UserProfileSerializer(user, context={"request": request})
        return Response(serializer.data)

    @extend_schema(responses=UserProfileSerializer, request=UserProfileSerializer)
    def patch(self, request):
        """Update the authenticated user's details."""
        user = self.get_object(request.user.pk)
        serializer = UserProfileSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UsersListView(APIView):
    """View to list all users."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer(many=True))
    def get(self, request):
        """List all users."""
        users = User.objects.all().prefetch_related("speakers_profile_user")
        user_filters = UserFilter(request.GET, queryset=users)
        qs = user_filters.qs

        from speakers.views import get_paginated_response, paginate_queryset

        page = paginate_queryset(self, qs)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return get_paginated_response(self, serializer.data)

        serializer = UserSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
