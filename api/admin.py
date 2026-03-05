from django.contrib import admin
from .models import (Node,Event, Identity, Profile,KeyPair, ErrorLog)

admin.site.register(Event)
admin.site.register(Identity)
admin.site.register(Profile)
admin.site.register(KeyPair)
admin.site.register(Node)

@admin.register(ErrorLog)
class ErrorLogModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at',)