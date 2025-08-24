"""user urls."""

from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("users/auth/register/", views.UserCreateView.as_view(), name="register"),
    path("users/auth/login/", views.UserLoginView.as_view(), name="login"),
    path("users/auth/logout/", views.UserLogoutView.as_view(), name="logout"),
]
