from django.db import models
from djongo import models as djongo_models
import uuid

class BaseProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=50, choices=[
        ('book', 'Book'),
        ('clothing', 'Clothing'),
        ('mobile', 'Mobile'),
    ])
    
    class Meta:
        abstract = True

class Book(BaseProduct):
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    pages = models.IntegerField()
    language = models.CharField(max_length=50)
    published_date = models.DateField()
    
    def __str__(self):
        return f"{self.name} by {self.author}"

class Clothing(BaseProduct):
    brand = models.CharField(max_length=100)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
        ('kids', 'Kids'),
    ])
    
    def __str__(self):
        return f"{self.brand} {self.name} ({self.color}, {self.size})"

class Mobile(BaseProduct):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    storage = models.CharField(max_length=50)
    ram = models.CharField(max_length=50)
    display = models.CharField(max_length=100)
    camera = models.CharField(max_length=100)
    battery = models.CharField(max_length=50)
    processor = models.CharField(max_length=100)
    operating_system = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.storage})"

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    product_type = models.CharField(max_length=20)  # 'book', 'clothing', 'mobile'
    image_url = models.URLField()
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product_type} {self.product_id}"