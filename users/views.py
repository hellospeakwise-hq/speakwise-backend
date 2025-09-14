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
from django.conf import settings
from rest_framework.decorators import api_view
from django.shortcuts import redirect
from requests_oauthlib import OAuth2Session

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



# OAuth2Session for GitHub
github = OAuth2Session(
    settings.GITHUB_CLIENT_ID,
    redirect_uri=settings.OAUTH2_REDIRECT_URI,
    scope=["public_repo", "read:user", "user:email"],
)

# OAuth2Session for Google
google = OAuth2Session(
    settings.GOOGLE_CLIENT_ID,
    redirect_uri=settings.OAUTH2_REDIRECT_URI,
    scope=["openid", "email", "profile"],
)

# OAuth endpoints
@api_view(["GET"])
def github_login(request):
    authorization_url, state = github.authorization_url("https://github.com/login/oauth/authorize")
    request.session["oauth_state"] = state
    return redirect(authorization_url)

@api_view(["GET"])

def github_callback(request):
    code = request.GET.get("code")
    role = request.GET.get("role")  # Optional role param
    github.fetch_token(
        "https://github.com/login/oauth/access_token",
        client_secret=settings.GITHUB_CLIENT_SECRET,
        code=code,
    )
    user_info = github.get("https://api.github.com/user").json()
    email = user_info.get("email")
    username = user_info.get("login")
    # Find or create user
    user, created = User.objects.get_or_create(email=email, defaults={"username": username})
    # Assign role and create profile if specified
    if role == UserRoleChoices.SPEAKER.value:
        SpeakerProfile.objects.get_or_create(user_account=user)
    elif role == UserRoleChoices.ORGANIZER.value:
        OrganizerProfile.objects.get_or_create(user_account=user)
    # TODO: Add JWT token response if needed
    return Response({"user": user_info, "role": role})


@api_view(["GET"])
def google_login(request):
    authorization_url, state = google.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
        prompt="select_account"
    )
    request.session["oauth_state"] = state
    return redirect(authorization_url)


@api_view(["GET"])
def google_callback(request):
    code = request.GET.get("code")
    role = request.GET.get("role")  # Optional role param
    google.fetch_token(
        "https://oauth2.googleapis.com/token",
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code,
    )
    user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    email = user_info.get("email")
    username = user_info.get("name")
    # Find or create user
    user, created = User.objects.get_or_create(email=email, defaults={"username": username})
    # Assign role and create profile if specified
    if role == UserRoleChoices.SPEAKER.value:
        SpeakerProfile.objects.get_or_create(user_account=user)
    elif role == UserRoleChoices.ORGANIZER.value:
        OrganizerProfile.objects.get_or_create(user_account=user)
    # TODO: Add JWT token response if needed
    return Response({"user": user_info, "role": role})


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
