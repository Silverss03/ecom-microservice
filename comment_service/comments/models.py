import uuid
from django.db import models
from django.utils import timezone

class EntityType(models.TextChoices):
    PRODUCT = 'PRODUCT', 'Product'
    ORDER = 'ORDER', 'Order'
    SHIPMENT = 'SHIPMENT', 'Shipment'
    BLOG = 'BLOG', 'Blog Post'

class CommentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Review'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    FLAGGED = 'FLAGGED', 'Flagged for Review'

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    entity_id = models.UUIDField()
    customer_id = models.UUIDField(null=True, blank=True)  # For anonymous comments
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(null=True, blank=True)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # For product reviews
    status = models.CharField(
        max_length=20, 
        choices=CommentStatus.choices,
        default=CommentStatus.PENDING
    )
    parent_comment = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_anonymous = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_aspects = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.customer_name} on {self.entity_type} {self.entity_id}"
    
    @property
    def has_replies(self):
        return self.replies.exists()
    
    @property
    def reply_count(self):
        return self.replies.count()

class CommentFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    customer_id = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comment', 'customer_id']
    
    def __str__(self):
        return f"Flag on comment {self.comment.id} by customer {self.customer_id}"