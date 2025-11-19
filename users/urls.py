"""user urls."""

from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("users/auth/register/", views.UserCreateView.as_view(), name="register"),
    path("users/auth/login/", views.UserLoginView.as_view(), name="login"),
    path("users/auth/logout/", views.UserLogoutView.as_view(), name="logout"),
    path(
        "users/auth/password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "users/auth/password-reset/confirm",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "users/me/",
        views.RetrieveUpdateAuthenticatedUserView.as_view(),
        name="retrieve_update_authenticated_user",
    ),
    path("users/", views.UsersListView.as_view(), name="user-list"),
]
