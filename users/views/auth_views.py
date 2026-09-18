"""users views."""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from base.permissions import IsEmailVerified
from users.filters import UserFilter
from users.models import User
from users.serializers import (
    LoginProfilesSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResendOtpSerializer,
    UserLoginSerializer,
    UserSerializer,
    VerifyOtpSerializer,
)
from users.services.auth_services import build_auth_payload, reset_email_verification
from users.services.otp_services import (
    issue_otp,
    resend_otp_by_email,
    send_otp_email,
    verify_otp_by_email,
)
from users.tasks import send_password_reset_email_task, send_welcome_email_task

GENERIC_PASSWORD_RESET_MESSAGE = "Password reset email sent successfully."
GENERIC_RESEND_OTP_MESSAGE = "A new verification code has been sent."
GENERIC_EMAIL_VERIFICATION_MESSAGE = "Please verify your email address."


@extend_schema(responses=UserSerializer)
class UserCreateView(APIView):
    """User create view."""

    permission_classes = [AllowAny]

    @extend_schema(request=UserSerializer, responses={201: UserSerializer})
    def post(self, request):
        """Create a new user and issue an email verification OTP."""
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        send_otp_email(user, issue_otp(user))

        data = build_auth_payload(user)

        # send welcome email task
        send_welcome_email_task.enqueue(str(user.id))
        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(request=VerifyOtpSerializer, responses={200: None})
class VerifyOtpView(APIView):
    """Verify an email address with a one-time password."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    def post(self, request):
        """Verify the submitted OTP and mark the user's email as verified."""
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify_otp_by_email(
            serializer.validated_data["email"], serializer.validated_data["otp"]
        )
        return Response(
            {"detail": "Email verified successfully."}, status=status.HTTP_200_OK
        )


@extend_schema(request=ResendOtpSerializer, responses={200: None})
class ResendOtpView(APIView):
    """Resend an email verification OTP code.

    Responds identically whether the email is unregistered, already verified,
    or inside the resend cooldown, so the endpoint does not reveal which
    addresses have accounts. The OTP business rules are unchanged; an email is
    only dispatched when all of them pass.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_resend"

    def post(self, request):
        """Issue and email a fresh OTP, respecting the resend cooldown."""
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user, code = resend_otp_by_email(email)
        except ValidationError:
            pass
        else:
            send_otp_email(user, code)
        return Response(
            {"detail": GENERIC_RESEND_OTP_MESSAGE}, status=status.HTTP_200_OK
        )


class UserLogoutView(APIView):
    """User logout view."""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        """Blacklist the user's refresh token."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError as exc:
            raise ValidationError({"detail": "Invalid refresh token."}) from exc
        return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(request=UserLoginSerializer, responses=UserSerializer)
class UserLoginView(APIView):
    """Log a user in with email and password, issuing JWT tokens.

    Provides the same behavior as the previous rst-auth-based login: a generic
    failure message (no account enumeration), the user's data in the response
    body, and their profiles reported under ``profile``.
    """

    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        """Authenticate the credentials and return the token payload."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        try:
            if not user.is_email_verified:
                return Response(
                    {"detail": GENERIC_EMAIL_VERIFICATION_MESSAGE},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValidationError as exc:
            raise ValidationError({"detail": exc.detail}) from exc
        data = build_auth_payload(user)
        data["profile"] = LoginProfilesSerializer(user).data
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(responses=PasswordResetRequestSerializer)
class PasswordResetRequestView(APIView):
    """Password request view for users.

    Always returns the same success response, whether the email is
    registered, so the endpoint does not reveal which addresses have accounts.
    The reset email is only dispatched when a matching user exists.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        """Request password reset for email."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.context.get("user")

        if user is not None:
            send_password_reset_email_task.enqueue(str(user.id))

        return Response(
            {"detail": GENERIC_PASSWORD_RESET_MESSAGE}, status=status.HTTP_200_OK
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

    def get_permissions(self):
        """Allow verified users to update; any authenticated user to read."""
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [IsAuthenticated()]
        return [IsEmailVerified()]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        """Retrieve the authenticated user's details."""
        user = get_object_or_404(User, id=request.user.pk)
        serializer = UserSerializer(user, context={"request": request})
        return Response(serializer.data)

    @extend_schema(responses=UserSerializer, request=UserSerializer)
    def patch(self, request):
        """Update the authenticated user's details.

        Changing the email address requires re-verification: the account is
        marked unverified and a fresh OTP is issued for the new address.
        """
        user = get_object_or_404(User, id=request.user.pk)
        previous_email = user.email
        serializer = UserSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        if serializer.instance.email != previous_email:
            reset_email_verification(updated_user)
        return Response(serializer.data)


class UsersListView(generics.ListAPIView):
    """List users, restricted to staff with global pagination."""

    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by("username")
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
