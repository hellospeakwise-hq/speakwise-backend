"""OAuth views."""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
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

logger = logging.getLogger(__name__)


def mobile_redirect(url: str) -> HttpResponse:
    """Return an HTML response that safely redirects mobile browsers to a custom app scheme."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Redirecting to SpeakWise...</title>
    <meta http-equiv="refresh" content="0;url={url}">
    <script>
        window.location.href = "{url}";
    </script>
</head>
<body style="background-color: #0d0d0d; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; padding: 24px; box-sizing: border-box;">
    <div style="background-color: #171717; border: 1px solid #262626; border-radius: 20px; padding: 32px 24px; max-width: 360px; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <h2 style="font-size: 22px; font-weight: 700; margin: 0 0 8px 0; color: #ffffff;">Authentication Successful</h2>
        <p style="color: #a0a0a0; font-size: 14px; margin: 0 0 24px 0; line-height: 1.5;">Opening the SpeakWise app...</p>
        <a href="{url}" style="display: block; padding: 14px 24px; background-color: #C5FF29; color: #000000; text-decoration: none; border-radius: 9999px; font-weight: 700; font-size: 15px; text-align: center;">Open SpeakWise App</a>
        <p style="color: #737373; font-size: 12px; margin: 16px 0 0 0;">If the app does not open automatically, tap the button above.</p>
    </div>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html", status=200)


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
    is_mobile = request.GET.get("platform") == "mobile"
    github = get_github_session()
    authorization_url, state = github.authorization_url(
        "https://github.com/login/oauth/authorize"
    )
    if is_mobile:
        orig_state = state
        state = f"mobile_{state}"
        authorization_url = authorization_url.replace(
            f"state={orig_state}", f"state={state}"
        )
        request.session["oauth_platform"] = "mobile"
        cache.set(f"oauth_state_{state}", "mobile", timeout=600)

    request.session["oauth_state"] = state
    return redirect(authorization_url)


def _github_email(github) -> tuple[str, str | None]:
    """Best-effort email from the GitHub profile, preferring a verified one.

    Raises ValidationError if the GitHub API requests fail.
    """
    try:
        user_info = github.get("https://api.github.com/user").json()
    except Exception as exc:
        raise ValidationError({"detail": "Failed to fetch GitHub user info."}) from exc

    email = user_info.get("email")
    username = user_info.get("login")
    if not email:
        try:
            emails_res = github.get("https://api.github.com/user/emails").json()
        except Exception as exc:
            raise ValidationError(
                {"detail": "Failed to fetch GitHub email addresses."}
            ) from exc
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

    cached_platform = cache.get(f"oauth_state_{state}")
    is_mobile = (
        (state and state.startswith("mobile_"))
        or cached_platform == "mobile"
        or request.session.get("oauth_platform") == "mobile"
    )

    is_valid_state = (
        state == request.session.get("oauth_state")
        or cached_platform is not None
        or (is_mobile and state and len(state) > 10)
    )

    if not state or not is_valid_state:
        return Response({"error": "Invalid state parameter"}, status=400)

    request.session.pop("oauth_state", None)
    request.session.pop("oauth_platform", None)

    try:
        github = get_github_session()
        github.fetch_token(
            "https://github.com/login/oauth/access_token",
            client_secret=settings.GITHUB_CLIENT_SECRET,
            code=code,
        )
        email, username = _github_email(github)

        user, _created = get_or_create_oauth_user(email=email, username=username)

        exchange_code = create_exchange_code(user)
        if is_mobile:
            return mobile_redirect(f"speakwise://auth/callback?code={exchange_code}")
        params = urlencode({"code": exchange_code})
        return redirect(f"{settings.FRONTEND_URL}/auth/callback?{params}")
    except ValidationError as exc:
        return Response(exc.detail, status=400)
    except Exception as exc:
        logger.exception("GitHub OAuth callback failed: %s", exc)
        return Response(
            {
                "error": "GitHub authentication failed. Please try again.",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
            status=400,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def google_login(request):
    """View to handle Google login."""
    is_mobile = request.GET.get("platform") == "mobile"
    google = get_google_session()
    authorization_url, state = google.authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        access_type="offline",
        prompt="select_account",
    )
    if is_mobile:
        orig_state = state
        state = f"mobile_{state}"
        authorization_url = authorization_url.replace(
            f"state={orig_state}", f"state={state}"
        )
        request.session["oauth_platform"] = "mobile"
        cache.set(f"oauth_state_{state}", "mobile", timeout=600)

    request.session["oauth_state"] = state
    return redirect(authorization_url)


@api_view(["GET"])
@permission_classes([AllowAny])
def google_callback(request):
    """View to handle Google callback."""
    code = request.GET.get("code")
    state = request.GET.get("state")

    cached_platform = cache.get(f"oauth_state_{state}")
    is_mobile = (
        (state and state.startswith("mobile_"))
        or cached_platform == "mobile"
        or request.session.get("oauth_platform") == "mobile"
    )

    is_valid_state = (
        state == request.session.get("oauth_state")
        or cached_platform is not None
        or (is_mobile and state and len(state) > 10)
    )

    if not state or not is_valid_state:
        return Response({"error": "Invalid state parameter"}, status=400)

    request.session.pop("oauth_state", None)
    request.session.pop("oauth_platform", None)

    try:
        google = get_google_session()
        google.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            code=code,
        )
        user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
        email = user_info.get("email")
        username = user_info.get("name")

        user, _created = get_or_create_oauth_user(email=email, username=username)

        exchange_code = create_exchange_code(user)
        if is_mobile:
            return mobile_redirect(f"speakwise://auth/callback?code={exchange_code}")
        params = urlencode({"code": exchange_code})
        return redirect(f"{settings.FRONTEND_URL}/auth/callback?{params}")
    except ValidationError as exc:
        return Response(exc.detail, status=400)
    except Exception as exc:
        logger.exception("Google OAuth callback failed: %s", exc)
        return Response(
            {
                "error": "Google authentication failed. Please try again.",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
            status=400,
        )


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
