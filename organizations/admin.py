"""Admin configuration for organizations app."""

from django.contrib import admin

from organizations.models import Organization, OrganizationMembership

# Register your models here.

admin.site.register(Organization)
admin.site.register(OrganizationMembership)
