from django.contrib import admin
from .models import Payment, PaymentHistory

class PaymentHistoryInline(admin.TabularInline):
    model = PaymentHistory
    extra = 0
    readonly_fields = ['timestamp']
    can_delete = False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'amount', 'currency', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'order_id', 'transaction_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [PaymentHistoryInline]
    fieldsets = (
        (None, {
            'fields': ('id', 'order_id', 'transaction_id', 'status')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'payment_method', 'payment_details')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment_id', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('payment__id', 'payment__order_id', 'notes')
    readonly_fields = ('id', 'timestamp')
    
    def payment_id(self, obj):
        return obj.payment.id
    payment_id.short_description = 'Payment ID'