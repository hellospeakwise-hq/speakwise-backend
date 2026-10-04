"""OAuth views."""

from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from requests_oauthlib import OAuth2Session
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from users.serializers import (
    LoginProfilesSerializer,
    OAuthCodeExchangeSerializer,
    UserSerializer,
)
from users.services.auth_services import build_auth_payload
from users.services.oauth_services import (
    consume_exchange_code,
    create_exchange_code,
    get_or_create_oauth_user,
)


def get_github_session():
    """Return a GitHub OAuth2Session."""
    return OAuth2Session(
        settings.GITHUB_CLIENT_ID,
        redirect_uri=settings.GITHUB_REDIRECT_URI,
        scope=["public_repo", "read:user", "user:email"],
    )


def get_google_session():
    """Return a Google OAuth2Session."""
    return OAuth2Session(
        settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        scope=[
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def github_login(request):
    """View to handle GitHub login."""
    github = get_github_session()
    authorization_url, state = github.authorization_url(
        "https://github.com/login/oauth/authorize"
    )
    request.session["oauth_state"] = state
    return redirect(authorization_url)


def _github_email(github) -> tuple[str, str | None]:
    """Best-effort email from the GitHub profile, preferring a verified one."""
    user_info = github.get("https://api.github.com/user").json()

    email = user_info.get("email")
    username = user_info.get("login")
    if not email:
        emails_res = github.get("https://api.github.com/user/emails").json()
        primary_emails = [
            e["email"] for e in emails_res if e.get("primary") and e.get("verified")
        ]
        if primary_emails:
            email = primary_emails[0]
        elif emails_res:
            email = emails_res[0].get("email")
    return email or "", username


@api_view(["GET"])
@permission_classes([AllowAny])
def github_callback(request):
    """View to handle GitHub callback."""
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not state or state != request.session.get("oauth_state"):
        return Response({"error": "Invalid state parameter"}, status=400)

    request.session.pop("oauth_state", None)

    github = get_github_session()
    github.fetch_token(
        "https://github.com/login/oauth/access_token",
        client_secret=settings.GITHUB_CLIENT_SECRET,
        code=code,
    )
    email, username = _github_email(github)

    try:
        user, _created = get_or_create_oauth_user(email=email, username=username)
    except ValidationError:
        return Response({"error": "Email not found from GitHub"}, status=400)

    params = urlencode({"code": create_exchange_code(user)})
    return redirect(f"{settings.FRONTEND_URL}/auth/callback?{params}")


@api_view(["GET"])
@permission_classes([AllowAny])
def google_login(request):
    """View to handle Google login."""
    google = get_google_session()
    authorization_url, state = google.authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        access_type="offline",
        prompt="select_account",
    )
    request.session["oauth_state"] = state
    return redirect(authorization_url)


@api_view(["GET"])
@permission_classes([AllowAny])
def google_callback(request):
    """View to handle Google callback."""
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not state or state != request.session.get("oauth_state"):
        return Response({"error": "Invalid state parameter"}, status=400)

    request.session.pop("oauth_state", None)

    google = get_google_session()
    google.fetch_token(
        "https://oauth2.googleapis.com/token",
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code,
    )
    user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    email = user_info.get("email")
    username = user_info.get("name")

    try:
        user, _created = get_or_create_oauth_user(email=email, username=username)
    except ValidationError:
        return Response({"error": "Email not found from Google"}, status=400)

    params = urlencode({"code": create_exchange_code(user)})
    return redirect(f"{settings.FRONTEND_URL}/auth/callback?{params}")


@extend_schema(request=OAuthCodeExchangeSerializer, responses=UserSerializer)
class OAuthTokenExchangeView(APIView):
    """Exchange a one-time OAuth code for JWT access and refresh tokens.

    The callback hands the frontend only a short-lived, single-use code; the
    real tokens are returned here in the response body so they never appear in
    URLs.
    """

    permission_classes = [AllowAny]
    serializer_class = OAuthCodeExchangeSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "oauth_token"

    def post(self, request):
        """Consume the code and return the token payload for its user."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = consume_exchange_code(serializer.validated_data["code"])
        data = build_auth_payload(user)
        data["profile"] = LoginProfilesSerializer(user).data
        return Response(data, status=status.HTTP_200_OK)
