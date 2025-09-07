"""event admin."""

from django.contrib import admin

# Register your models here.
from events.models import Country, Event, Tag

admin.site.register(Event)
admin.site.register(Country)
admin.site.register(Tag)
