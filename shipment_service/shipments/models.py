from django.db import models
import uuid
from datetime import datetime, timedelta
import random
import string

class ShipmentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    READY_FOR_PICKUP = 'READY_FOR_PICKUP', 'Ready for Pickup'
    IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
    DELIVERED = 'DELIVERED', 'Delivered'
    FAILED = 'FAILED', 'Failed Delivery'
    RETURNED = 'RETURNED', 'Returned'
    CANCELLED = 'CANCELLED', 'Cancelled'

class ShippingProvider(models.TextChoices):
    EXPRESS = 'EXPRESS', 'Express Shipping'
    STANDARD = 'STANDARD', 'Standard Shipping'
    ECONOMY = 'ECONOMY', 'Economy Shipping'

class Shipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField()
    tracking_number = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING
    )
    shipping_provider = models.CharField(
        max_length=20,
        choices=ShippingProvider.choices,
        default=ShippingProvider.STANDARD
    )
    shipping_address = models.JSONField()
    shipping_date = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # in kg
    dimensions = models.JSONField(null=True, blank=True)  # {'length': x, 'width': y, 'height': z} in cm
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generate tracking number on first save
        if not self.tracking_number:
            self.tracking_number = self._generate_tracking_number()
        
        # Calculate estimated delivery date if shipping date is set but estimated delivery isn't
        if self.shipping_date and not self.estimated_delivery:
            self.estimated_delivery = self._calculate_estimated_delivery()
        
        super().save(*args, **kwargs)
    
    def _generate_tracking_number(self):
        """Generate a unique tracking number for the shipment"""
        prefix = self.shipping_provider[:2]
        timestamp = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Format: {PROVIDER_PREFIX}-{DATE}-{RANDOM_STRING}
        tracking_number = f"{prefix}-{timestamp}-{random_str}"
        
        # Ensure uniqueness
        while Shipment.objects.filter(tracking_number=tracking_number).exists():
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            tracking_number = f"{prefix}-{timestamp}-{random_str}"
            
        return tracking_number
    
    def _calculate_estimated_delivery(self):
        """Calculate the estimated delivery date based on shipping provider"""
        from django.conf import settings
        
        provider_config = settings.SHIPPING_PROVIDERS.get(self.shipping_provider, {})
        min_days, max_days = provider_config.get('estimated_days', [3, 7])
        
        # Generate a random number of days between min and max
        delivery_days = random.randint(min_days, max_days)
        
        return self.shipping_date + timedelta(days=delivery_days)
    
    def get_tracking_url(self):
        """Generate a tracking URL for the shipment"""
        from django.conf import settings
        
        provider_config = settings.SHIPPING_PROVIDERS.get(self.shipping_provider, {})
        base_url = provider_config.get('tracking_url', '')
        
        if base_url:
            return f"{base_url}{self.tracking_number}"
        return None
    
    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.status}"

class ShipmentUpdate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=20, choices=ShipmentStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status} at {self.timestamp}"