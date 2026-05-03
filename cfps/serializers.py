"""CFP serializers."""

from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from cfps.choices import CFPStatusChoices
from cfps.models import CFPSubmission
from speakers.models import SpeakerProfile


class CoSpeakerSerializer(serializers.ModelSerializer):
    """Minimal read-only representation of a co-speaker."""

    name = serializers.SerializerMethodField()

    class Meta:
        """Meta options for CoSpeakerSerializer."""

        model = SpeakerProfile
        fields = ["id", "slug", "name"]

    def get_name(self, obj):
        """Return the co-speaker's full name or username."""
        return (
            f"{obj.user_account.first_name} {obj.user_account.last_name}".strip()
            or obj.user_account.username
        )


class CFPSubmissionSerializer(WritableNestedModelSerializer):
    """Serializer for creating and reading CFP submissions."""

    co_speakers = serializers.PrimaryKeyRelatedField(
        queryset=SpeakerProfile.objects.all(), many=True, required=False
    )
    co_speakers_detail = CoSpeakerSerializer(
        source="co_speakers", many=True, read_only=True
    )
    submitter_email = serializers.EmailField(source="submitter.email", read_only=True)

    class Meta:
        """Meta options for CFPSubmissionSerializer."""

        model = CFPSubmission
        exclude = ["created_at", "updated_at"]
        read_only_fields = ["id", "submitter", "submitter_email", "status", "event"]

    def update(self, instance, validated_data):
        """Update a CFP submission, only allowed while pending."""
        if instance.status != CFPStatusChoices.PENDING:
            raise serializers.ValidationError(
                "Submissions can only be edited while they are pending review."
            )
        return super().update(instance, validated_data)


class CFPStatusUpdateSerializer(serializers.ModelSerializer):
    """Organizer-only serializer for updating submission status."""

    class Meta:
        """Meta options for CFPStatusUpdateSerializer."""

        model = CFPSubmission
        fields = ["status"]
