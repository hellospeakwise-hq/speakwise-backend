"""user urls."""

from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("users/auth/register/", views.UserCreateView.as_view(), name="register"),
    path("users/auth/login/", views.UserLoginView.as_view(), name="login"),
    path("users/auth/logout/", views.UserLogoutView.as_view(), name="logout"),
    path("users/auth/github-login/", views.github_login, name="github-login"),
    path("users/auth/github-callback/", views.github_callback, name="github-callback"),
    path("users/auth/google-login/", views.google_login, name="google-login"),
    path("users/auth/google-callback/", views.google_callback, name="google-callback"),
]
