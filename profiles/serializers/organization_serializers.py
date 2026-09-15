"""Organization serializers for user profiles."""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from profiles.models.organization_models import OrganizationCFP, OrganizationProfile
from profiles.models.speaker_models import SpeakerProfile


class OrganizationCFPSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationCFP model."""

    class Meta:
        """Meta-options for OrganizationCFPSerializer."""

        model = OrganizationCFP
        fields = ["url", "description", "open_at", "close_at"]


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationProfile model."""

    cfps = OrganizationCFPSerializer(read_only=True, required=False)

    class Meta:
        """Meta-options for OrganizationProfileSerializer."""

        model = OrganizationProfile
        fields = [
            "id",
            "owner",
            "name",
            "description",
            "website",
            "branding",
            "contact_email",
            "status",
            "admin_notes",
            "cfps",
        ]
        read_only_fields = ["owner", "status", "admin_notes", "id"]

    def create(self, validated_data):
        """Create the organization profile owned by the requesting user.

        A user is allowed to have one and only one profile: they cannot create an
        organization profile when they already have a speaker profile, nor can
        they own more than one organization. The owner is always the requesting
        user — it can never be supplied by the client.
        """
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            raise ValidationError(
                {"detail": "Must be authenticated to create a profile."}
            )

        user = request.user
        if SpeakerProfile.objects.filter(user_account=user).exists():
            raise ValidationError(
                {
                    "detail": "User already has a speaker profile; a user can "
                    "have only one profile."
                }
            )
        if OrganizationProfile.objects.filter(owner=user).exists():
            raise ValidationError(
                {"detail": "Organization profile already exists for this user."}
            )

        validated_data["owner"] = user
        return super().create(validated_data)
