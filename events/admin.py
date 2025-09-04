"""event admin."""

from django.contrib import admin

# Register your models here.
from events.models import Country, Event, Session, Tag

admin.site.register(Event)
admin.site.register(Session)
admin.site.register(Country)
admin.site.register(Tag)
