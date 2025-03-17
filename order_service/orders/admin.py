from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['timestamp']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_id', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer_id')
    readonly_fields = ('id', 'order_number', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    fieldsets = (
        (None, {
            'fields': ('id', 'order_number', 'customer_id', 'status', 'total_amount')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Address Information', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_details')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_type', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('product_type',)
    search_fields = ('order__order_number', 'product_id')

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp', 'comment')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__order_number', 'comment')
    readonly_fields = ('timestamp',)