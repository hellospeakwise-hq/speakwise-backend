"""CFP serializers."""

from rest_framework import serializers

from cfp.choices import CFPStatusChoices
from cfp.models import CFPSubmission
from speakers.models import SpeakerProfile


class CoSpeakerSerializer(serializers.ModelSerializer):
    """Minimal read-only representation of a co-speaker."""

    name = serializers.SerializerMethodField()

    class Meta:
        model = SpeakerProfile
        fields = ["id", "slug", "name"]

    def get_name(self, obj):
        return f"{obj.user_account.first_name} {obj.user_account.last_name}".strip() or obj.user_account.username


class CFPSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating and reading CFP submissions."""

    co_speakers = serializers.PrimaryKeyRelatedField(
        queryset=SpeakerProfile.objects.all(), many=True, required=False
    )
    co_speakers_detail = CoSpeakerSerializer(source="co_speakers", many=True, read_only=True)
    submitter_email = serializers.EmailField(source="submitter.email", read_only=True)

    class Meta:
        model = CFPSubmission
        exclude = ["created_at", "updated_at"]
        read_only_fields = ["id", "submitter", "submitter_email", "status", "event"]

    def create(self, validated_data):
        co_speakers = validated_data.pop("co_speakers", [])
        submission = CFPSubmission.objects.create(**validated_data)
        submission.co_speakers.set(co_speakers)
        return submission

    def update(self, instance, validated_data):
        if instance.status != CFPStatusChoices.PENDING:
            raise serializers.ValidationError(
                "Submissions can only be edited while they are pending review."
            )
        co_speakers = validated_data.pop("co_speakers", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if co_speakers is not None:
            instance.co_speakers.set(co_speakers)
        return instance


class CFPStatusUpdateSerializer(serializers.ModelSerializer):
    """Organizer-only serializer for updating submission status."""

    class Meta:
        model = CFPSubmission
        fields = ["status"]
