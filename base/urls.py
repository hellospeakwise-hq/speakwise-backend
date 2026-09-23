"""Base URLs for shared endpoints."""

from django.urls import path

from base.views import HealthCheckView

app_name = "base"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
]
