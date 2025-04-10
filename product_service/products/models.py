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

class ProductSentiment(models.Model):
    product = models.OneToOneField('Product', on_delete=models.CASCADE, related_name='sentiment')
    avg_sentiment_score = models.FloatField(default=0.0)
    review_count = models.IntegerField(default=0)
    
    # Aggregate sentiment by aspects
    aspect_sentiment = models.JSONField(default=dict)
    
    # Store top positive and negative aspects
    top_positive_aspects = models.JSONField(default=list)
    top_negative_aspects = models.JSONField(default=list)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_with_sentiment(self, sentiment_score, aspects, rating=None):
        """Update the sentiment aggregations with new data"""
        # Update average sentiment (weighted running average)
        total = self.avg_sentiment_score * self.review_count
        self.review_count += 1
        self.avg_sentiment_score = (total + sentiment_score) / self.review_count
        
        # Update aspect sentiment
        for aspect in aspects:
            if aspect in self.aspect_sentiment:
                aspect_data = self.aspect_sentiment[aspect]
                # Update running average for this aspect
                total = aspect_data['score'] * aspect_data['count']
                aspect_data['count'] += 1
                aspect_data['score'] = (total + sentiment_score) / aspect_data['count']
                # Update last mention timestamp
                aspect_data['last_mentioned'] = timezone.now().isoformat()
            else:
                self.aspect_sentiment[aspect] = {
                    'score': sentiment_score,
                    'count': 1,
                    'last_mentioned': timezone.now().isoformat()
                }
        
        # Recalculate top positive and negative aspects
        self._recalculate_top_aspects()
        
        self.save()
    
    def _recalculate_top_aspects(self, limit=5):
        """Recalculate top positive and negative aspects"""
        # Get aspects with at least 2 mentions
        frequent_aspects = {k: v for k, v in self.aspect_sentiment.items() 
                            if v['count'] >= 2}
        
        # Sort by score (descending for positive, ascending for negative)
        sorted_aspects = sorted(frequent_aspects.items(), 
                              key=lambda x: x[1]['score'], 
                              reverse=True)
        
        # Get top positive and negative aspects
        self.top_positive_aspects = [
            {'aspect': a[0], 'score': a[1]['score']} 
            for a in sorted_aspects[:limit] 
            if a[1]['score'] > 0
        ]
        
        self.top_negative_aspects = [
            {'aspect': a[0], 'score': a[1]['score']} 
            for a in reversed(sorted_aspects)[:limit] 
            if a[1]['score'] < 0
        ]