"""users admin."""

from django.contrib import admin

from users.models import User, UserRole


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """user admin."""

    fields = ["username", "email"]
    search_fields = ["nationality", "role", "email"]
    list_display = ["username", "email", "role"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """user role admin."""

    fields = ["role"]
    search_fields = ["role"]
    list_display = ["role"]
