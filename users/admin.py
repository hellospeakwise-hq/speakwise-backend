"""users admin."""

from django.contrib import admin

from users.models import User


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
