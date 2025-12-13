"""OAuth views."""

from django.conf import settings
from django.shortcuts import redirect
from requests_oauthlib import OAuth2Session
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# No UserRoleChoices import as requested
from rest_framework_simplejwt.tokens import RefreshToken

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


@api_view(["GET"])
@permission_classes([AllowAny])
def github_login(request):
    """View to handle GitHub login."""
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

    github.fetch_token(
        "https://github.com/login/oauth/access_token",
        client_secret=settings.GITHUB_CLIENT_SECRET,
        code=code,
    )
    user_info = github.get("https://api.github.com/user").json()

    email = user_info.get("email")
    username = user_info.get("login")
    if not email:
        return Response({"error": "Email not found from GitHub"}, status=400)

    # Find or create user
    user, created = User.objects.get_or_create(
        email=email, defaults={"username": username}
    )

    # Generate Tokens
    refresh = RefreshToken.for_user(user)
    # Add extra payload if needed, similar to LoginBaseClass
    refresh.payload.update(UserSerializer(user).data)

    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
            "message": "Login successful",
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def google_login(request):
    """View to handle Google login."""
    authorization_url, state = google.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
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

    google.fetch_token(
        "https://oauth2.googleapis.com/token",
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code,
    )
    user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    email = user_info.get("email")
    username = user_info.get("name")

    # Find or create user
    user, created = User.objects.get_or_create(
        email=email, defaults={"username": username}
    )

    # Generate Tokens
    refresh = RefreshToken.for_user(user)
    refresh.payload.update(UserSerializer(user).data)

    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
            "message": "Login successful",
        }
    )
