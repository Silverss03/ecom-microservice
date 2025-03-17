import uuid
import base64
from rest_framework import serializers
from .models import Cart, CartItem

class UUIDField(serializers.Field):
    """Field that can accept both UUID strings and Base64-encoded UUID binary"""
    
    def to_internal_value(self, data):
        try:
            # Try parsing as regular UUID string
            return uuid.UUID(data)
        except (ValueError, AttributeError):
            try:
                # Try parsing as Base64
                binary_data = base64.b64decode(data)
                return uuid.UUID(bytes=binary_data)
            except:
                raise serializers.ValidationError("Invalid UUID format")
    
    def to_representation(self, value):
        return str(value)

class CartItemSerializer(serializers.ModelSerializer):
    product_id = UUIDField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product_type', 'quantity', 
                  'name', 'price', 'image_url', 'added_at', 'subtotal']
        read_only_fields = ['id', 'name', 'price', 'image_url', 'added_at', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'customer_id', 'items', 'total_price', 'total_items', 
                  'created_at', 'updated_at', 'expires_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'expires_at']

class AddToCartSerializer(serializers.Serializer):
    product_id = UUIDField()
    product_type = serializers.ChoiceField(choices=[('book', 'Book'), 
                                                    ('clothing', 'Clothing'), 
                                                    ('mobile', 'Mobile')])
    quantity = serializers.IntegerField(min_value=1, default=1)

class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)

class CartMergeSerializer(serializers.Serializer):
    source_cart_id = serializers.UUIDField()
    destination_cart_id = serializers.UUIDField()