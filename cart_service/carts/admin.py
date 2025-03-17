from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['id', 'subtotal']
    
    def subtotal(self, obj):
        return obj.subtotal
    
    subtotal.short_description = 'Subtotal'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_id', 'total_items', 'total_price', 'created_at', 'updated_at', 'expires_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['id', 'customer_id']
    readonly_fields = ['id', 'total_price', 'total_items', 'created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def total_price(self, obj):
        return obj.total_price
    
    def total_items(self, obj):
        return obj.total_items
    
    total_price.short_description = 'Total Price'
    total_items.short_description = 'Total Items'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product_type', 'product_id', 'name', 'quantity', 'price', 'subtotal', 'added_at']
    list_filter = ['product_type', 'added_at']
    search_fields = ['cart__id', 'name', 'product_id']
    readonly_fields = ['id', 'subtotal', 'added_at']
    
    def subtotal(self, obj):
        return obj.subtotal
    
    subtotal.short_description = 'Subtotal'