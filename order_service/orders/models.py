from django.db import models
import uuid

class OrderStatus(models.TextChoices):
    CREATED = 'CREATED', 'Created'
    PROCESSING = 'PROCESSING', 'Processing'
    PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
    PAID = 'PAID', 'Paid'
    SHIPPED = 'SHIPPED', 'Shipped'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELED = 'CANCELED', 'Canceled'
    REFUNDED = 'REFUNDED', 'Refunded'

class PaymentMethod(models.TextChoices):
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    DEBIT_CARD = 'DEBIT_CARD', 'Debit Card'
    PAYPAL = 'PAYPAL', 'PayPal'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
    CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', 'Cash on Delivery'

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer_id = models.UUIDField()  # Reference to customer service
    status = models.CharField(
        max_length=20, 
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.JSONField()  # Store shipping address as JSON
    billing_address = models.JSONField(null=True, blank=True)  # Optional billing address
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )
    payment_details = models.JSONField(null=True, blank=True)  # Store payment details as JSON
    notes = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Generate order number on first save
        if not self.order_number:
            # Format: ORD-{year}{month}{day}-{random_6_digits}
            from datetime import datetime
            import random
            now = datetime.now()
            rand = random.randint(100000, 999999)
            self.order_number = f"ORD-{now.strftime('%Y%m%d')}-{rand}"
        
        # Calculate total if order items exist and this is an update
        if self.pk:  # If the object has already been created
            self.total_amount = sum(item.subtotal for item in self.items.all())
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField()  # Reference to product service
    product_type = models.CharField(max_length=20)  # 'book', 'clothing', 'mobile'
    product_data = models.JSONField()  # Store product details as JSON for order history
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update order total
        self.order.save()
    
    def __str__(self):
        return f"{self.quantity} x {self.product_data.get('name', 'Unknown Product')}"

class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=OrderStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.timestamp}"