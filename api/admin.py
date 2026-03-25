from django.contrib import admin
from .models import (Node,Transaction, Identity, KeyPair, ErrorLog)



# admin.site.register(Transaction)
# admin.site.register(Identity)
# admin.site.register(Vote)
admin.site.register(KeyPair)
admin.site.register(Node)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    ordering = ('-height',)

@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = ('public_key','balance','balance_from_txns')

@admin.register(ErrorLog)
class ErrorLogModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at',)
