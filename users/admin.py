"""users admin."""

import io

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from users.models import User
from users.services.auth_services import stale_unverified_users, write_users_csv

DEFAULT_PURGE_DAYS = 30


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """user admin."""

    fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "password",
        "nationality",
        "is_email_verified",
    ]

    search_fields = ["nationality", "email", "first_name", "last_name", "username"]
    list_display = ["username", "email", "first_name", "last_name", "nationality"]
    list_filter = ["is_email_verified", "nationality"]
    change_list_template = "admin/users/user/change_list.html"

    def get_urls(self):
        """Add the purge-unverified-users page next to the default admin URLs."""
        custom = [
            path(
                "purge-unverified/",
                self.admin_site.admin_view(self.purge_unverified_view),
                name="users_user_purge_unverified",
            ),
        ]
        return custom + super().get_urls()

    def purge_unverified_view(self, request):
        """Preview and delete stale never-verified accounts (superusers only)."""
        if not request.user.is_superuser:
            messages.error(request, "Only superusers can purge accounts.")
            return redirect(reverse("admin:users_user_changelist"))

        raw_days = request.POST.get("days") or request.GET.get("days")
        try:
            days = max(int(raw_days), 1) if raw_days else DEFAULT_PURGE_DAYS
        except ValueError:
            days = DEFAULT_PURGE_DAYS
        queryset = stale_unverified_users(days)

        if request.method == "POST" and request.POST.get("confirm") == "yes":
            user_ids = list(queryset.values_list("pk", flat=True))
            if not user_ids:
                messages.info(request, "Nothing to delete.")
                return redirect(reverse("admin:users_user_changelist"))

            backup = io.StringIO()
            write_users_csv(backup, queryset)
            User.objects.filter(pk__in=user_ids).delete()
            stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
            response = HttpResponse(backup.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="purged_unverified_users_{stamp}.csv"'
            )
            return response

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Purge unverified users",
            "days": days,
            "count": queryset.count(),
            "preview": queryset.order_by("date_joined")[:50],
        }
        return TemplateResponse(
            request, "admin/users/user/purge_unverified.html", context
        )
