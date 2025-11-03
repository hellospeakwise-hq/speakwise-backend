"""Serializers for the feedback app."""

from email.policy import default
from os import write
from rest_framework import serializers

from attendees.models import Attendance
from feedbacks.models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with support for anonymous feedback."""

    class Meta:
        """Meta options."""

        model = Feedback
        exclude = ["created_at", "updated_at"]
        extra_kwargs = {
            "email": {"required": False, "write_only": True},
            "is_anonymous": {"required": False, "read_only": True},
            "is_attendee": {"required": False, "read_only": True},
        }

    def validate(self, data):
        """Validate data."""

        if "email" not in data:
            data["is_anonymous"] = True  # set anonymous if email not provided
            return data

        try:
            attendance = Attendance.objects.get(email=data["email"])
            if not attendance.is_given_feedback:
                data["is_attendee"] = True  # set attendee flag to true
                attendance.is_given_feedback = True  # set feedback given to true
                attendance.save()
            else:
                # prevent multiple feedback submissions
                return {"error": "Feedback has already been submitted with this email."}
            return data
        except Attendance.DoesNotExist:
            data["is_anonymous"] = True  # set anonymous if email not found
            return data
