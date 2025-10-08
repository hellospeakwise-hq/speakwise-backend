"""user serializers."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

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
        ]
        extra_kwargs = {"password": {"write_only": True}, "id": {"read_only": True}}


class UserLoginSerializer(serializers.Serializer):
    """User login serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset via email."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate that the provided email is associated with a user."""
        try:
            User.objects.get(email=value)
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

    def validate(self, data):
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
