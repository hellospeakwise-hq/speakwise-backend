"""OAuth views."""

import json
import os
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from requests_oauthlib import OAuth2Session
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.serializers import UserSerializer

frontend_url = os.environ.get("FRONTEND_URL")


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


@api_view(["GET"])
@permission_classes([AllowAny])
def github_callback(request):
    """View to handle GitHub callback."""
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not state or state != request.session.get("oauth_state"):
        return Response({"error": "Invalid state parameter"}, status=400)

    github = get_github_session()
    github.fetch_token(
        "https://github.com/login/oauth/access_token",
        client_secret=settings.GITHUB_CLIENT_SECRET,
        code=code,
    )
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

    if not email:
        return Response({"error": "Email not found from GitHub"}, status=400)

    user = User.objects.filter(email=email).first()
    if not user:
        user = User.objects.create(email=email, username=username)

    refresh = RefreshToken.for_user(user)
    refresh.payload.update(UserSerializer(user).data)

    params = urlencode(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": json.dumps(UserSerializer(user).data),  # ← FIXED: Convert dict to JSON string
        }
    )
    return redirect(f"{frontend_url}/auth/callback?{params}")  # ← FIXED: Added /auth/callback


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

    google = get_google_session()
    google.fetch_token(
        "https://oauth2.googleapis.com/token",
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code,
    )
    user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    email = user_info.get("email")
    username = user_info.get("name")

    user = User.objects.filter(email=email).first()
    if not user:
        user = User.objects.create(email=email, username=username)

    refresh = RefreshToken.for_user(user)
    refresh.payload.update(UserSerializer(user).data)

    params = urlencode(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": json.dumps(UserSerializer(user).data),  # ← Convert dict to JSON string
        }
    )
    return redirect(f"{frontend_url}/auth/callback?{params}")  #  Added /auth/callback