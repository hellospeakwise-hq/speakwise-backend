"""user serializers."""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.validators import RegexValidator
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from profiles.serializers.organization_serializers import OrganizationProfileSerializer
from profiles.serializers.speaker_serializers import SpeakerProfileSerializer
from users.models import User
from users.services.auth_services import authenticate_user


class UserSerializer(WritableNestedModelSerializer):
    """User model serializer."""

    class Meta:
        """Meta class."""

        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "nationality",
            "username",
            "password",
            "is_email_verified",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "id": {"read_only": True},
            "is_email_verified": {"read_only": True},
        }

    def validate_password(self, value) -> str:
        """Enforce the project password policy for new registrations."""
        validate_password(value)
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer that authenticates a user with their email and password.

    Credential verification and the failed-login lockout are delegated to
    :func:`users.auth_services.authenticate_user`; a successful login exposes
    the resolved user through ``validated_data["user"]``.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs) -> dict:
        """Authenticate the credentials and attach the user to the attrs."""
        user = authenticate_user(
            attrs["email"],
            attrs["password"],
            request=self.context.get("request"),
        )
        attrs["user"] = user
        return attrs


class VerifyOtpSerializer(serializers.Serializer):
    """Serializer for verifying an email address with an OTP code."""

    email = serializers.EmailField()
    otp = serializers.CharField(
        max_length=settings.OTP_CODE_LENGTH,
        min_length=settings.OTP_CODE_LENGTH,
        validators=[
            RegexValidator(r"^\d+$", message="OTP code must contain only digits.")
        ],
        trim_whitespace=False,
    )


class ResendOtpSerializer(serializers.Serializer):
    """Serializer for requesting a new OTP code."""

    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset via email.

    The response and behaviour must not reveal whether an email address is
    registered, so validation never fails on an unknown email. The matched
    user (when one exists) is exposed through ``context["user"]``.
    """

    email = serializers.EmailField()

    def validate_email(self, value) -> str:
        """Look up the user for the email without leaking its existence."""
        user = User.objects.filter(email=value).first()
        if user is not None:
            self.context["user"] = user
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset with email, token, and new password."""

    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs) -> dict:
        """Validate the provided email and token, and ensure the user exists."""
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No user is associated with this email address."
            ) from None

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired token.")

        validate_password(attrs["new_password"], user=user)

        self.context["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Serializer for logging out a user by blacklisting a refresh token."""

    refresh = serializers.CharField(write_only=True)


class OAuthCodeExchangeSerializer(serializers.Serializer):
    """Serializer for exchanging a one-time OAuth code for tokens."""

    code = serializers.CharField(write_only=True)


class LoginProfilesSerializer(serializers.Serializer):
    """Detect and serialize a user's speaker and organization profiles.

    Returns the profile data attached to the user so login flows can report
    which profile exists. A user can hold one and only one profile, so each
    field is either the profile object or ``None``.
    """

    speaker_profile = SpeakerProfileSerializer(
        source="speakers_profile_user", read_only=True, allow_null=True
    )
    organization_profile = OrganizationProfileSerializer(
        source="organization_owner", read_only=True, allow_null=True
    )

    def to_representation(self, instance):
        """Omit the profile keys that hold no data.

        Login responses should report only the profile a user actually has.
        """
        data = super().to_representation(instance)
        return {key: value for key, value in data.items() if value is not None}
