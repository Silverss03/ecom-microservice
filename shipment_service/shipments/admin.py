from django.contrib import admin
from .models import Shipment, ShipmentUpdate

class ShipmentUpdateInline(admin.TabularInline):
    model = ShipmentUpdate
    extra = 0
    readonly_fields = ['timestamp']
    fields = ['status', 'timestamp', 'location', 'description']

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order_id', 'status', 'shipping_provider', 
                    'shipping_date', 'estimated_delivery', 'actual_delivery')
    list_filter = ('status', 'shipping_provider', 'created_at')
    search_fields = ('tracking_number', 'order_id')
    readonly_fields = ('id', 'tracking_number', 'created_at', 'updated_at', 'get_tracking_url')
    inlines = [ShipmentUpdateInline]
    fieldsets = (
        (None, {
            'fields': ('id', 'order_id', 'tracking_number', 'status', 'get_tracking_url')
        }),
        ('Shipping Details', {
            'fields': ('shipping_provider', 'shipping_address', 'weight', 'dimensions')
        }),
        ('Dates', {
            'fields': ('shipping_date', 'estimated_delivery', 'actual_delivery', 'created_at', 'updated_at')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )
    
    def get_tracking_url(self, obj):
        url = obj.get_tracking_url()
        if url:
            return f'<a href="{url}" target="_blank">{url}</a>'
        return 'Not available'
    get_tracking_url.allow_tags = True
    get_tracking_url.short_description = 'Tracking URL'

@admin.register(ShipmentUpdate)
class ShipmentUpdateAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'timestamp', 'location')
    list_filter = ('status', 'timestamp')
    search_fields = ('shipment__tracking_number', 'shipment__order_id', 'location', 'description')
    readonly_fields = ('id', 'timestamp')