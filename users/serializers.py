"""user serializers."""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.validators import RegexValidator
from drf_spectacular.utils import extend_schema_field
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from profiles.serializers.organization_serializers import OrganizationProfileSerializer
from profiles.serializers.speaker_serializers import SpeakerProfileSerializer
from profiles.services.organization_services import get_owned_organizations
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

    def validate_email(self, value: str) -> str:
        """Normalize email address to lowercase and trimmed."""
        return value.strip().lower()

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

    A user can hold one speaker profile and own several organizations, in any
    combination. ``organization_profiles`` lists every owned organization,
    oldest first.
    """

    speaker_profile = SpeakerProfileSerializer(
        source="speakers_profile_user", read_only=True, allow_null=True
    )
    organization_profiles = serializers.SerializerMethodField()
    # Deprecated: kept so frontends reading the old single-organization key keep
    # working while they move to organization_profiles. Remove in a follow-up.
    organization_profile = serializers.SerializerMethodField()

    def _serialized_organizations(self, instance) -> list:
        """Serialize the user's organizations once and reuse it for both keys.

        Cached per user so a ``many=True`` parent, which reuses one child
        serializer for every user, never mixes users' organizations.
        """
        cache = self.__dict__.setdefault("_organizations_by_user", {})
        if instance.pk not in cache:
            cache[instance.pk] = OrganizationProfileSerializer(
                get_owned_organizations(instance), many=True
            ).data
        return cache[instance.pk]

    @extend_schema_field(OrganizationProfileSerializer(many=True))
    def get_organization_profiles(self, instance) -> list:
        """Return every organization the user owns, or None when they own none."""
        return self._serialized_organizations(instance) or None

    @extend_schema_field(OrganizationProfileSerializer(allow_null=True))
    def get_organization_profile(self, instance):
        """Return the user's oldest organization (deprecated single-org key)."""
        organizations = self._serialized_organizations(instance)
        return organizations[0] if organizations else None

    def to_representation(self, instance):
        """Omit the profile keys that hold no data.

        Login responses should report only the profiles a user actually has.
        """
        data = super().to_representation(instance)
        return {key: value for key, value in data.items() if value is not None}
