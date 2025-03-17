import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Cart {self.id} - Customer: {self.customer_id or 'Guest'}"
    
    def save(self, *args, **kwargs):
        # Set expiration date for guest carts
        if not self.customer_id and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=settings.CART_EXPIRY_DAYS)
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def is_empty(self):
        return self.items.count() == 0

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product_id = models.UUIDField()
    product_type = models.CharField(max_length=20)  # 'book', 'clothing', 'mobile'
    quantity = models.PositiveIntegerField(default=1)
    
    # Product information snapshot (stored at add time)
    name = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'product_id', 'product_type')
    
    def __str__(self):
        return f"{self.quantity} x {self.name or self.product_id}"
    
    @property
    def subtotal(self):
        return self.price * self.quantity if self.price else 0