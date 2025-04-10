from rest_framework import serializers
from .models import Comment, CommentFlag, EntityType, CommentStatus

class CommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'customer_name', 'content', 'created_at', 'updated_at', 'status']
        read_only_fields = ['id', 'created_at', 'updated_at', 'status']

class CommentSerializer(serializers.ModelSerializer):
    replies = CommentReplySerializer(many=True, read_only=True)
    reply_count = serializers.IntegerField(read_only=True)
    has_replies = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'entity_type', 'entity_id', 'customer_id', 'customer_name', 
            'customer_email', 'content', 'rating', 'status', 'created_at', 
            'updated_at', 'is_anonymous', 'parent_comment', 'replies', 
            'reply_count', 'has_replies'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status']
    
    def validate(self, data):
        entity_type = data.get('entity_type')
        
        # Validate entity_type is supported
        if entity_type not in [choice[0] for choice in EntityType.choices]:
            raise serializers.ValidationError(f"Unsupported entity type: {entity_type}")
        
        # Rating is only allowed for product comments
        if entity_type != EntityType.PRODUCT and data.get('rating') is not None:
            raise serializers.ValidationError("Rating is only allowed for product comments")
        
        # Validate rating range if provided
        rating = data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        
        return data
    
    def create(self, validated_data):
        # Get IP from request if available
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
        
        # Set is_anonymous based on customer_id
        if not validated_data.get('customer_id'):
            validated_data['is_anonymous'] = True
        
        # Create comment
        comment = Comment.objects.create(**validated_data)
        return comment
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            'entity_type', 'entity_id', 'customer_id', 'customer_name', 
            'customer_email', 'content', 'rating', 'parent_comment'
        ]
    
    def validate(self, data):
        # If this is a reply, validate parent exists and is approved
        parent_comment = data.get('parent_comment')
        if parent_comment:
            if parent_comment.status != CommentStatus.APPROVED:
                raise serializers.ValidationError("Cannot reply to an unapproved comment")
            
            # Ensure reply is for the same entity
            if (data.get('entity_type') != parent_comment.entity_type or 
                data.get('entity_id') != parent_comment.entity_id):
                raise serializers.ValidationError("Reply must be for the same entity as parent comment")
            
            # Disallow nested replies (only one level deep)
            if parent_comment.parent_comment:
                raise serializers.ValidationError("Nested replies are not allowed")
        
        return data

class CommentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CommentStatus.choices)
    
class CommentFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentFlag
        fields = ['id', 'comment', 'customer_id', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']