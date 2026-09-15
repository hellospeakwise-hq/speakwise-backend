"""user serializers."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.validators import RegexValidator
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from profiles.serializers.organization_serializers import OrganizationProfileSerializer
from profiles.serializers.speaker_serializers import SpeakerProfileSerializer
from users.models import User


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


class UserLoginSerializer(serializers.Serializer):
    """User login serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


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
    """Serializer for requesting a password reset via email."""

    email = serializers.EmailField()

    def validate_email(self, value) -> str:
        """Validate that the provided email is associated with a user."""
        try:
            user = User.objects.get(email=value)
            self.context["user"] = user
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No user is associated with this email address."
            ) from None
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset with email, token, and new password."""

    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data) -> dict:
        """Validate the provided email and token, and ensure the user exists."""
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No user is associated with this email address."
            ) from None

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError("Invalid or expired token.")

        self.context["user"] = user
        return data


class UserProfileSerializer(UserSerializer):
    """Serializer for user profile."""

    speaker = SpeakerProfileSerializer(source="speakers_profile_user", required=False)

    class Meta:
        """meta options."""

        model = User
        exclude = ["password"]


class LogoutSerializer(serializers.Serializer):
    """Serializer for logging out a user by blacklisting a refresh token."""

    refresh = serializers.CharField(write_only=True)


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
