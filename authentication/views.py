"""Authentication views for the Nebula app."""

from abc import ABC
from abc import abstractmethod
import json

from dj_rest_auth.views import LoginView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_simplejwt.tokens import RefreshToken

# TODO from attendees.models import Attendee
# TODO from attendees.serializers import AttendeeSerializer
from speakers.models import SpeakerProfile
from speakers.serializers import SpeakerProfileSerializer

from authentication.exceptions import AuthenticationError


class LoginBaseClass(ABC, LoginView):
    """This class inherits the LoginView from the rest_auth package.
    Django rest auth lib does not support the refresh token
    logic. However,restframework_simplejwt does. Rest auth was
    used because it's based off all-auth which can be used for
    social logins as well as signing in with either username or
    password(of which simplejwt does not support). The two libraries
    were combined to give the required results.
    """

    def get_extra_payload(self) -> dict:
        """This method is used to add extra payload to the refresh token."""
        return {}

    def get_token(self, user):
        """Generate the refresh token."""
        refresh_token = RefreshToken.for_user(user)
        for key, value in self.get_extra_payload().items():
            refresh_token[key] = value
        return refresh_token

    @abstractmethod
    def login(self):
        """Login in the user."""

    def get_response(self):
        """Return the response with the refresh token."""
        data = {}

        refresh = self.get_token(self.user)
        # generate access and refresh tokens
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        return Response(data)


class OrganizerLoginView(LoginBaseClass):
    """Login view for organizers."""

    def login(self):
        """Login the organizer."""
        self.user = self.serializer.validated_data["user"]
        if not self.user.role or self.user.role.display != "organizer":
            raise AuthenticationError
        return self.user

    # def get_extra_payload(self) -> dict:
    #     """Return the organizer data."""
    #     try:
    #         admin = self.user.role.users_role.get(role__display="organizer")
    #     except UserRole.DoesNotExist as err:
    #         raise AuthenticationError from err
    #     serializer = UserSerializer(admin)
    #     return {"organizer": serializer.data}


class AttendeeLoginView(LoginBaseClass):
    """Login view for attendees."""

    def login(self):
        """Login the attendee."""
        self.user = self.serializer.validated_data["user"]
        if not self.user.role or self.user.role.display != "attendee":
            raise AuthenticationError
        return self.user

    # TODO: def get_extra_payload(self) -> dict:
    #     """Return the attendee data."""
    #     try:
    #         attendee = Attendee.objects.get(user=self.user)
    #     except Attendee.DoesNotExist as err:
    #         raise AuthenticationError from err
    #     serializer = AttendeeSerializer(attendee)
    #     return {"attendee": serializer.data}


class SpeakerLoginView(LoginBaseClass):
    """Login view for speaker."""

    def login(self):
        """Login the speaker."""
        self.user = self.serializer.validated_data["user"]
        if not self.user.role or self.user.role.role != "speaker":
            raise AuthenticationError
        return self.user

    def get_extra_payload(self) -> dict:
        """Return the speaker data."""
        try:
            speaker = SpeakerProfile.objects.get(user_account=self.user)
        except SpeakerProfile.DoesNotExist as err:
            raise AuthenticationError from err
        serializer = SpeakerProfileSerializer(speaker)

        speaker_data = json.loads(JSONRenderer().render(serializer.data))
        return speaker_data
