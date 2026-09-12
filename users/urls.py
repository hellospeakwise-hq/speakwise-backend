"""user urls."""

from django.urls import path

from users.views import auth_views, oauth_views

app_name = "users"

urlpatterns = [
    path("users/auth/register/", auth_views.UserCreateView.as_view(), name="register"),
    path("users/auth/login/", auth_views.UserLoginView.as_view(), name="login"),
    path("users/auth/logout/", auth_views.UserLogoutView.as_view(), name="logout"),
    path("users/auth/github-login/", oauth_views.github_login, name="github-login"),
    path(
        "users/auth/github-callback/",
        oauth_views.github_callback,
        name="github-callback",
    ),
    path("users/auth/google-login/", oauth_views.google_login, name="google-login"),
    path(
        "users/auth/google-callback/",
        oauth_views.google_callback,
        name="google-callback",
    ),
    path(
        "users/auth/password-reset/",
        auth_views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "users/auth/password-reset/confirm",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "users/me/",
        auth_views.RetrieveUpdateAuthenticatedUserView.as_view(),
        name="retrieve_update_authenticated_user",
    ),
    path("users/", auth_views.UsersListView.as_view(), name="user-list"),
]
