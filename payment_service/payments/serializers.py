from rest_framework import serializers
from .models import Payment, PaymentHistory, PaymentMethod, PaymentStatus

class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = ['id', 'status', 'timestamp', 'notes']
        read_only_fields = ['id', 'timestamp']

class PaymentSerializer(serializers.ModelSerializer):
    history = PaymentHistorySerializer(many=True, read_only=True)
    payment_details_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'amount', 'currency', 'payment_method',
                  'status', 'payment_details', 'payment_details_display',
                  'transaction_id', 'created_at', 'updated_at', 'history']
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at', 'history']
    
    def get_payment_details_display(self, obj):
        """Return a sanitized version of payment details for display"""
        if not obj.payment_details:
            return {}
        
        # Create a copy to avoid modifying the original
        display_details = dict(obj.payment_details)
        
        # Mask sensitive data
        if 'card_number' in display_details:
            display_details['card_number'] = obj.mask_card_number(display_details['card_number'])
        
        # Remove CVV
        if 'cvv' in display_details:
            display_details['cvv'] = '***'
            
        return display_details

class PaymentCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    card_number = serializers.CharField(required=False, max_length=16, min_length=13)
    expiry_date = serializers.CharField(required=False, max_length=7)  # MM/YYYY
    cvv = serializers.CharField(required=False, max_length=4, min_length=3)
    card_holder_name = serializers.CharField(required=False, max_length=100)
    
    # For cash on delivery, bank transfer
    notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Payment
        fields = ['order_id', 'amount', 'currency', 'payment_method', 
                  'card_number', 'expiry_date', 'cvv', 'card_holder_name', 'notes']
    
    def validate(self, data):
        """Validate payment details based on payment method"""
        payment_method = data.get('payment_method')
        
        # Validate credit/debit card details
        if payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
            required_fields = ['card_number', 'expiry_date', 'cvv', 'card_holder_name']
            for field in required_fields:
                if field not in data or not data[field]:
                    raise serializers.ValidationError(f"{field} is required for card payments")
        
        return data
    
    def create(self, validated_data):
        """Create a new payment"""
        # Extract payment details
        payment_details = {}
        detail_fields = ['card_number', 'expiry_date', 'cvv', 'card_holder_name', 'notes']
        
        for field in detail_fields:
            if field in validated_data:
                payment_details[field] = validated_data.pop(field)
        
        # Add payment method to details
        payment_details['method'] = validated_data.get('payment_method')
        
        # Create payment
        payment = Payment.objects.create(
            **validated_data,
            payment_details=payment_details
        )
        
        # Create initial history entry
        PaymentHistory.objects.create(
            payment=payment,
            status=payment.status,
            notes="Payment initiated"
        )
        
        return payment

class ProcessPaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()

class RefundPaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=255, required=False)