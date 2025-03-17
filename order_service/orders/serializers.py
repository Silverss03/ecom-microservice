from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_type', 'product_data', 
                  'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['subtotal']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'timestamp', 'comment']
        read_only_fields = ['timestamp']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer_id', 'status', 'created_at', 
                  'updated_at', 'total_amount', 'shipping_address', 'billing_address', 
                  'payment_method', 'payment_details', 'notes', 'items', 'status_history']
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at', 'total_amount']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['customer_id', 'shipping_address', 'billing_address', 'notes', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        # Create initial status history entry
        OrderStatusHistory.objects.create(
            order=order,
            status=order.status,
            comment="Order created"
        )
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Recalculate total (triggers save method)
        order.save()
        
        return order

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatusHistory.status.field.choices)
    comment = serializers.CharField(required=False, allow_blank=True)