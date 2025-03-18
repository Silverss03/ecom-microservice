from rest_framework import serializers
from .models import Shipment, ShipmentUpdate, ShipmentStatus, ShippingProvider

class ShipmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentUpdate
        fields = ['id', 'status', 'timestamp', 'location', 'description']
        read_only_fields = ['id', 'timestamp']

class ShipmentSerializer(serializers.ModelSerializer):
    updates = ShipmentUpdateSerializer(many=True, read_only=True)
    tracking_url = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Shipment
        fields = ['id', 'order_id', 'tracking_number', 'status', 
                  'shipping_provider', 'provider_name', 'shipping_address', 
                  'shipping_date', 'estimated_delivery', 'actual_delivery',
                  'tracking_url', 'weight', 'dimensions', 'notes',
                  'created_at', 'updated_at', 'updates']
        read_only_fields = ['id', 'tracking_number', 'created_at', 'updated_at', 
                           'tracking_url', 'provider_name']
    
    def get_tracking_url(self, obj):
        return obj.get_tracking_url()
    
    def get_provider_name(self, obj):
        from django.conf import settings
        provider_config = settings.SHIPPING_PROVIDERS.get(obj.shipping_provider, {})
        return provider_config.get('name', obj.shipping_provider)

class ShipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ['order_id', 'shipping_provider', 'shipping_address', 
                  'weight', 'dimensions', 'notes']
    
    def create(self, validated_data):
        # Create the shipment
        shipment = Shipment.objects.create(**validated_data)
        
        # Add initial status update
        ShipmentUpdate.objects.create(
            shipment=shipment,
            status=ShipmentStatus.PENDING,
            description="Shipment created and pending processing"
        )
        
        return shipment

class UpdateShipmentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ShipmentStatus.choices)
    location = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)

class ProcessShipmentSerializer(serializers.Serializer):
    shipment_id = serializers.UUIDField()

class DeliverShipmentSerializer(serializers.Serializer):
    shipment_id = serializers.UUIDField()
    proof_of_delivery = serializers.CharField(required=False)