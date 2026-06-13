"""user serializers."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers

from speakers.models import SpeakerProfile
from speakers.serializers import SpeakerProfileSerializer
from users.models import User


class UserSerializer(serializers.ModelSerializer):
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
        ]
        extra_kwargs = {"password": {"write_only": True}, "id": {"read_only": True}}


class UserLoginSerializer(serializers.Serializer):
    """User login serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


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

    speaker = SpeakerProfileSerializer(
        source="speakers_profile_user", many=True, required=False
    )

    class Meta:
        """meta options."""

        model = User
        exclude = ["password"]

    def update(self, instance, validated_data):
        """Update user and nested speaker profile data."""
        speaker_data = validated_data.pop("speakers_profile_user", None)
        user = super().update(instance, validated_data)

        if speaker_data:
            for profile_data in speaker_data:
                profile_id = profile_data.get("id")
                if profile_id:
                    SpeakerProfile.objects.filter(
                        pk=profile_id, user_account=user
                    ).update(**profile_data)
                else:
                    SpeakerProfile.objects.update_or_create(
                        user_account=user,
                        defaults=profile_data,
                    )
        return user


class LogoutSerializer(serializers.Serializer):
    """Serializer for logging out a user by blacklisting a refresh token."""

    refresh = serializers.CharField(write_only=True)
