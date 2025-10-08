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
    ]
    search_fields = ["nationality", "role", "email"]
    list_display = ["username", "email", "first_name", "last_name", "nationality"]
