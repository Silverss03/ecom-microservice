from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
import requests
import json

from .models import Order, OrderItem, OrderStatusHistory, OrderStatus
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer,
    OrderItemSerializer
)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate customer exists
        customer_id = serializer.validated_data['customer_id']
        customer_exists = self._validate_customer(customer_id)
        if not customer_exists:
            return Response(
                {"detail": "Customer not found"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate products exist and have stock
        items_data = serializer.validated_data.get('items', [])
        invalid_items = self._validate_products(items_data)
        if invalid_items:
            return Response(
                {"detail": "Invalid products", "invalid_items": invalid_items},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch and enhance product details
        self._enhance_product_data(items_data)
        
        # Create the order
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            comment = serializer.validated_data.get('comment', '')
            
            # Update order status
            order.status = new_status
            order.save()
            
            # Create status history entry
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                comment=comment
            )
            
            # If the order is canceled, perhaps we could restore inventory
            if new_status == OrderStatus.CANCELED:
                self._handle_cancellation(order)
                
            return Response({
                'status': 'status updated',
                'new_status': new_status
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        order = self.get_object()
        history = order.status_history.all()
        from .serializers import OrderStatusHistorySerializer
        serializer = OrderStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    def _validate_customer(self, customer_id):
        """Validate customer exists by calling customer service"""
        # In a real-world scenario, you'd make an API call to the customer service
        try:
            customer_service_url = f"{settings.MICROSERVICE_URLS['CUSTOMER_SERVICE']}/customers/{customer_id}/"
            response = requests.get(customer_service_url)
            return response.status_code == 200
        except requests.RequestException:
            # Log the error but continue - fault tolerance in microservices
            return True  # Assume customer exists if service is down
    
    def _validate_products(self, items_data):
        """Validate products exist and have stock"""
        invalid_items = []
        
        for item in items_data:
            product_id = item['product_id']
            product_type = item['product_type']
            quantity = item['quantity']
            
            # Check if product exists and has enough stock
            try:
                product_service_url = f"{settings.MICROSERVICE_URLS['PRODUCT_SERVICE']}/{product_type}s/{product_id}/"
                response = requests.get(product_service_url)
                
                if response.status_code != 200:
                    invalid_items.append({
                        'product_id': product_id,
                        'reason': 'Product not found'
                    })
                    continue
                
                product_data = response.json()
                if product_data['stock_quantity'] < quantity:
                    invalid_items.append({
                        'product_id': product_id,
                        'reason': 'Insufficient stock',
                        'available': product_data['stock_quantity'],
                        'requested': quantity
                    })
            except requests.RequestException:
                # Log the error but continue - fault tolerance
                pass
                
        return invalid_items
    
    def _enhance_product_data(self, items_data):
        """Fetch full product details from product service"""
        for item in items_data:
            product_id = item['product_id']
            product_type = item['product_type']
            
            try:
                product_service_url = f"{settings.MICROSERVICE_URLS['PRODUCT_SERVICE']}/{product_type}s/{product_id}/"
                response = requests.get(product_service_url)
                
                if response.status_code == 200:
                    product_data = response.json()
                    # Store relevant product data for order history
                    item['product_data'] = {
                        'id': product_data['id'],
                        'name': product_data['name'],
                        'price': product_data['price'],
                        'category': product_data['category'],
                        # Add more fields as needed
                    }
                    # Set unit price from product data
                    item['unit_price'] = product_data['price']
            except requests.RequestException:
                # Log the error but continue
                # Use placeholder data if service is down
                item['product_data'] = {
                    'id': product_id,
                    'name': 'Unknown Product',
                }
    
    def _handle_cancellation(self, order):
        """Handle order cancellation - could restore inventory"""
        # This would typically call the product service to restore stock
        pass

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    
    def get_queryset(self):
        queryset = OrderItem.objects.all()
        order_id = self.request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        return queryset