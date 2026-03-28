from django.contrib import admin
from .models import Item, SimulatorDetails

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_code', 'category', 'availability', 'assigned_quantity', 'total_quantity')
    search_fields = ('name', 'item_code')
    list_filter = ('category', 'availability')


admin.site.register(SimulatorDetails)
