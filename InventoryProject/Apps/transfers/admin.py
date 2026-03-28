from django.contrib import admin
from .models import Transfer, TransferAuditLog

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('item', 'sender', 'receiver', 'status', 'transfer_date', 'expected_date')
    list_filter = ('status', 'from_office', 'to_office')
    search_fields = ('item__name', 'item__item_code', 'serial_number', 'sender__name', 'receiver__name')


admin.site.register(TransferAuditLog)
