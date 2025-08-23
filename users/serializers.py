"""user serializers."""

from rest_framework import serializers
from users.models import User, UserRole
from drf_writable_nested.serializers import WritableNestedModelSerializer

# from attendees.models import Attendee
# from attendees.serializers import AttendeeSerializer

# from organizers.models import Organizers
# from organizers.serializers import OrganizersSerializer


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
        fields = ["id", "username", "email", "password", "role"]
        extra_kwargs = {"password": {"write_only": True}, "id": {"read_only": True}}

    def create(self, validated_data):
        """Create a new user."""
        role_data = validated_data.pop("role")
        password = validated_data.pop("password")
        # Look up the UserRole by display value and assign to user
        if role_data and "role" in role_data:
            role_obj, _ = UserRole.objects.get_or_create(role=role_data["role"])
            print("ROLE OBJ: ", role_obj)
            validated_data["role"] = role_obj
        user = User.objects.create(password=password, **validated_data)

        # Create Attendee profile if role is attendee
        if role_data and role_data.get("display") == "attendee":
            ...

        # Create or get attendee with the user's email
        # attendee, created = Attendee.objects.get_or_create(
        #     email=user.email,
        #     defaults={
        #         "user": user,
        #         "first_name": user.first_name,
        #         "last_name": user.last_name,
        #     },
        # )
        # if not created:
        # If attendee already exists, just associate it with the user
        # attendee.user = user
        # attendee.save()

        # Create SpeakerProfile if role is speaker
        elif role_data and role_data.get("role") == "speaker":
            from speakers.models import SpeakerProfile

            # Create speaker profile for the user
            SpeakerProfile.objects.create(
                user_account=user,
                long_bio="",  # Required field, set to empty initially
            )

        # Create OrganizerProfile if role is organizer
        elif role_data and role_data.get("display") == "organizer":
            ...

        # Create organizer profile for the user
        # Organizers.objects.create(
        #     user_id=user,
        #     organization="",  # Required field, set to empty initially
        # )

        return user


class UserLoginSerializer(serializers.Serializer):
    """User login serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
