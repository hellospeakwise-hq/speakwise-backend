"""user urls."""

from django.urls import path
from users import views

app_name = "users"

urlpatterns = [
    path("users/register/", views.UserCreateView.as_view(), name="register"),
    path("users/logout/", views.UserLogoutView.as_view(), name="logout"),
]
