"""users views."""

import json
from abc import ABC, abstractmethod

from dj_rest_auth.views import LoginView
from django.contrib.auth import logout
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from attendees.models import AttendeeProfile
from attendees.serializers import AttendeeProfileSerializer
from organizers.models import OrganizerProfile
from organizers.serializers import OrganizerProfileSerializer
from speakers.models import SpeakerProfile
from speakers.serializers import SpeakerProfileSerializer
from users.choices import UserRoleChoices
from users.exceptions import AuthenticationError
from users.models import User
from users.serializers import UserSerializer


@extend_schema(responses=UserSerializer)
class UserCreateView(CreateAPIView):
    """User create view."""

    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]


class UserLogoutView(APIView):
    """User logout view."""

    def post(self, request):
        """Logout user."""
        refresh = request.data.get("refresh")
        if refresh is None:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh)
            token.blacklist()
            logout(request)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


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
        data.update(self.get_extra_payload())

        return Response(data)


class UserLoginView(LoginBaseClass):
    """Login view for speaker."""

    def login(self):
        """Login the speaker."""
        self.user = self.serializer.validated_data["user"]
        if not self.user.role or self.user.role.role not in [
            UserRoleChoices.SPEAKER.value,
            UserRoleChoices.ATTENDEE.value,
            UserRoleChoices.ORGANIZER.value,
        ]:
            raise AuthenticationError
        return self.user

    def get_extra_payload(self) -> dict:
        """Return the speaker data."""
        if self.user.role.role == UserRoleChoices.SPEAKER.value:
            serializer = SpeakerProfileSerializer(
                SpeakerProfile.objects.get(user_account=self.user)
            )
        elif self.user.role.role == UserRoleChoices.ATTENDEE.value:
            serializer = AttendeeProfileSerializer(
                AttendeeProfile.objects.get(user_account=self.user)
            )
        elif self.user.role.role == UserRoleChoices.ORGANIZER.value:
            serializer = OrganizerProfileSerializer(
                OrganizerProfile.objects.get(user_account=self.user)
            )
        else:
            return {}
        user_data = json.loads(JSONRenderer().render(serializer.data))
        return user_data
