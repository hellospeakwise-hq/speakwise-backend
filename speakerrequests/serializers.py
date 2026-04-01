"""speaker request serializers."""

from rest_framework import serializers

from events.models import Event  # Assuming Event model is in events.models
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from users.models import User  # Assuming User model is in users.models


class SpeakerRequestSerializer(serializers.ModelSerializer):
    """speaker request serializer for output (read-only)."""

    organization_name = serializers.CharField(source="organizer.name", read_only=True)
    speaker_name = serializers.CharField(
        source="speaker.user_account.get_full_name", read_only=True
    )
    event_title = serializers.CharField(source="event.title", read_only=True)

    organization_name = serializers.CharField(source="organizer.name", read_only=True)
    speaker_name = serializers.CharField(source="speaker.user_account.get_full_name", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        fields = [
            "id",
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
            "organizer",
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
>>>>>>> 7255978 (refactor speakerrequest API)
=======
            "organizer",
>>>>>>> 9e60841 (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
            "organization_name",
            "speaker",
            "speaker_name",
            "event",
            "event_title",
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            "organizer",
=======
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
            "organizer",
>>>>>>> 7255978 (refactor speakerrequest API)
=======
>>>>>>> 9e60841 (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
            "status",
            "message",
            "created_at",
            "updated_at",
        ]
<<<<<<< HEAD
        read_only_fields = fields  # All fields are read-only for this output serializer


class SpeakerRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SpeakerRequest (input)."""

    class Meta:
        model = SpeakerRequest
        fields = [
            "speaker",
            "event",
            "message",
        ]


class SpeakerRequestRespondSerializer(serializers.Serializer):
    """Serializer for responding to a speaker request (input)."""

    status = serializers.ChoiceField(choices=RequestStatusChoices.choices)
=======
        read_only_fields = ["status", "created_at", "updated_at"]
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)


class EmailRequestsSerializer(serializers.ModelSerializer):
    """Email request serializer for output (read-only)."""

    request_from_username = serializers.CharField(
        source="request_from.username", read_only=True
    )
    request_to_username = serializers.CharField(
        source="request_to.username", read_only=True
    )

    class Meta:
        """Meta class for email request serializer."""

        model = SpeakerEmailRequests
        fields = [
            "id",
            "event",
            "location",
            "request_from",
            "request_from_username",
            "request_to",
            "request_to_username",
            "message",
            "status",
        ]
        read_only_fields = fields  # All fields are read-only for this output serializer

<<<<<<< HEAD

class EmailRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating email requests (input)."""

    request_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = SpeakerEmailRequests
        fields = ["request_to", "event", "message"]


class EmailRequestsRespondSerializer(serializers.Serializer):
    """Serializer for responding to an email request (input)."""

    status = serializers.ChoiceField(choices=RequestStatusChoices.choices)
=======
    def validate(self, attrs):
        """Validate email request data."""
        if not attrs.get("request_to") and not attrs.get("request_from"):
             raise serializers.ValidationError(
                {"error": "request_to and request_from are required."}
            )
        return attrs
<<<<<<< HEAD

<<<<<<< HEAD
>>>>>>> 8dfda2b (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
=======
>>>>>>> 7255978 (refactor speakerrequest API)
=======
>>>>>>> 9e60841 (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
