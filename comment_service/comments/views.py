import requests
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Count

from .models import Comment, CommentFlag, CommentStatus, EntityType
from .serializers import (
    CommentSerializer, CommentCreateSerializer, 
    CommentStatusUpdateSerializer, CommentFlagSerializer
)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.filter(parent_comment=None)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'customer_name']
    ordering_fields = ['created_at', 'updated_at', 'rating']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter top-level comments only by default (no replies)
        queryset = queryset.filter(parent_comment=None)
        
        # Annotate with reply count
        queryset = queryset.annotate(
            reply_count=Count('replies')
        )
        
        # Filter by entity type and ID if provided
        entity_type = self.request.query_params.get('entity_type')
        entity_id = self.request.query_params.get('entity_id')
        
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        # Filter by customer ID if provided
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            # By default, only show approved comments
            queryset = queryset.filter(status=CommentStatus.APPROVED)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Validate entity exists by calling the appropriate service
        entity_type = serializer.validated_data['entity_type']
        entity_id = serializer.validated_data['entity_id']
        
        entity_exists = self._validate_entity(entity_type, entity_id)
        if not entity_exists:
            return Response(
                {"detail": f"{entity_type} with ID {entity_id} not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-approve comments for now (can be changed to require moderation)
        comment = serializer.save(status=CommentStatus.APPROVED)
        
        # If this is a product review with rating, notify product service
        if entity_type == EntityType.PRODUCT and serializer.validated_data.get('rating'):
            self._notify_product_rating(
                entity_id, 
                serializer.validated_data['rating']
            )
        
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a comment (for moderation)"""
        comment = self.get_object()
        serializer = CommentStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            
            # Update comment status
            comment.status = new_status
            comment.save()
            
            # If rejecting, also reject all replies
            if new_status == CommentStatus.REJECTED:
                comment.replies.all().update(status=CommentStatus.REJECTED)
            
            return Response({
                'status': 'status updated',
                'new_status': new_status
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """Flag a comment for review"""
        comment = self.get_object()
        
        # Create flag data with comment ID
        data = {
            'comment': comment.id,
            **request.data
        }
        
        serializer = CommentFlagSerializer(data=data)
        if serializer.is_valid():
            # Create the flag
            serializer.save()
            
            # Update comment status to flagged
            comment.status = CommentStatus.FLAGGED
            comment.save()
            
            return Response({
                'status': 'comment flagged for review',
                'flag': serializer.data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies for a comment"""
        comment = self.get_object()
        replies = comment.replies.filter(status=CommentStatus.APPROVED)
        serializer = CommentSerializer(replies, many=True)
        return Response(serializer.data)
    
    def _validate_entity(self, entity_type, entity_id):
        """Validate entity exists by calling the appropriate service"""
        try:
            if entity_type == EntityType.PRODUCT:
                # Try each product type endpoint since we don't know which type it is
                for product_type in ['books', 'clothing', 'mobiles']:
                    endpoint = f"{settings.MICROSERVICE_URLS['PRODUCT_SERVICE']}/{product_type}/{entity_id}/"
                    response = requests.get(endpoint)
                    if response.status_code == 200:
                        return True
                
                # No matching product found in any category
                return False
                    
            elif entity_type == EntityType.ORDER:
                response = requests.get(f"{settings.MICROSERVICE_URLS['ORDER_SERVICE']}/orders/{entity_id}/")
                return response.status_code == 200
                
            elif entity_type == EntityType.SHIPMENT:
                response = requests.get(f"{settings.MICROSERVICE_URLS['SHIPMENT_SERVICE']}/shipments/{entity_id}/")
                return response.status_code == 200
                
            # Add more entity types as needed
            return True  # Default to true for unimplemented types
            
        except requests.RequestException as e:
            # Log error but continue (assume entity exists if service is down)
            print(f"Error validating entity: {str(e)}")
            return True
    
    def _notify_product_rating(self, product_id, rating):
        """Notify product service about a new product rating"""
        try:
            url = f"{settings.MICROSERVICE_URLS['PRODUCT_SERVICE']}/products/{product_id}/rate/"
            requests.post(url, json={'rating': rating})
        except requests.RequestException:
            # Log error but don't fail the request
            pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sentiment_service = SentimentAnalysisService()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Analyze sentiment using your CNN model
        content = serializer.validated_data['content']
        sentiment_data = self.sentiment_service.analyze_text(content)
        
        # Save comment with sentiment data
        comment = serializer.save(
            sentiment_score=sentiment_data['normalized_score'],
            sentiment_aspects=sentiment_data['aspects']
        )
        
        # Push sentiment data to product service for recommendations
        self._notify_product_service(comment, sentiment_data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    def _notify_product_service(self, comment, sentiment_data):
        """Send sentiment data to product service"""
        if comment.entity_type != 'product':
            return
            
        try:
            url = f"{settings.SERVICE_URLS['product_service']}/api/products/{comment.entity_id}/sentiment/"
            data = {
                'comment_id': str(comment.id),
                'user_id': str(comment.user_id),
                'rating': comment.rating,
                'sentiment_score': sentiment_data['normalized_score'],
                'sentiment_aspects': sentiment_data['aspects']
            }
            requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error notifying product service: {e}")

class CommentFlagViewSet(viewsets.ModelViewSet):
    queryset = CommentFlag.objects.all().order_by('-created_at')
    serializer_class = CommentFlagSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by comment ID if provided
        comment_id = self.request.query_params.get('comment_id')
        if comment_id:
            queryset = queryset.filter(comment_id=comment_id)
        
        # Filter by customer ID if provided
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset