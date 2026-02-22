from django.contrib import admin
from .models import (Event, Identity, Profile)

admin.site.register(Event)
admin.site.register(Identity)
admin.site.register(Profile)