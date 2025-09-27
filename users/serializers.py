"""user serializers."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from attendees.models import AttendeeProfile
from organizers.models import OrganizerProfile
from users.choices import UserRoleChoices
from users.models import User, UserRole


class UserRoleSerializer(serializers.ModelSerializer):
    """UserRole model serializer."""

    class Meta:
        """Meta class."""

        model = UserRole
        fields = ["id", "role"]


class UserSerializer(WritableNestedModelSerializer):
    """User model serializer."""

    role = UserRoleSerializer()

    class Meta:
        """Meta class."""

        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "username",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}, "id": {"read_only": True}}

    def create(self, validated_data):
        """Create a new user."""
        role_data = validated_data.pop("role")
        password = validated_data.pop("password")
        user = None

        # Look up the UserRole by display value and assign to user
        if role_data and "role" in role_data:
            role_obj, _ = UserRole.objects.get_or_create(role=role_data["role"])
            print("ROLE OBJ: ", role_obj)
            validated_data["role"] = role_obj
            user = User.objects.create(password=password, **validated_data)

        # Create Attendee profile if role is attendee
        if role_data and role_data.get("role") == UserRoleChoices.ATTENDEE.value:
            # Create or get attendee with the user's email
            attendee, created = AttendeeProfile.objects.get_or_create(
                email=user.email,
                defaults={"user_account": user},
            )

        # Create SpeakerProfile if role is speaker
        elif role_data and role_data.get("role") == UserRoleChoices.SPEAKER.value:
            from speakers.models import SpeakerProfile

            # Create speaker profile for the user
            SpeakerProfile.objects.create(
                user_account=user,
                long_bio="",  # Required field, set to empty initially
            )

        # Create OrganizerProfile if role is organizer
        elif role_data and role_data.get("role") == UserRoleChoices.ORGANIZER.value:
            # Create organizer profile for the user
            OrganizerProfile.objects.create(
                user_account=user,
                organization="",  # Required field, set to empty initially
            )

        return user


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
