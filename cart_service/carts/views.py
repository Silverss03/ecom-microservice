import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import Cart, CartItem
from .serializers import (
    CartSerializer, AddToCartSerializer, 
    UpdateCartItemSerializer, CartMergeSerializer
)

class CartView(APIView):
    def get(self, request, cart_id=None):
        """Get cart contents"""
        if cart_id:
            # Get specific cart
            cart = get_object_or_404(Cart, id=cart_id)
        elif request.user.is_authenticated:
            # Get or create customer cart
            cart, _ = Cart.objects.get_or_create(
                customer_id=request.user.id,
                defaults={'expires_at': None}
            )
        else:
            return Response(
                {"error": "Cart ID required for guest users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Clean up expired items (optional)
        self._clean_stale_items(cart)
            
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request, cart_id=None):
        """Add item to cart"""
        # Get or create cart
        if cart_id:
            cart = get_object_or_404(Cart, id=cart_id)
        elif request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(
                customer_id=request.user.id,
                defaults={'expires_at': None}
            )
        else:
            # Create new cart for guest
            cart = Cart.objects.create()
        
        # Validate input
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            # Get product data
            product_data = self._get_product_data(
                serializer.validated_data['product_id'],
                serializer.validated_data['product_type']
            )
            
            if not product_data:
                return Response(
                    {"error": "Product not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check stock
            if product_data.get('stock_quantity', 0) < serializer.validated_data['quantity']:
                return Response(
                    {"error": f"Insufficient stock. Only {product_data.get('stock_quantity')} available."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add to cart
            with transaction.atomic():
                item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product_id=serializer.validated_data['product_id'],
                    product_type=serializer.validated_data['product_type'],
                    defaults={
                        'quantity': serializer.validated_data['quantity'],
                        'name': product_data.get('name'),
                        'price': product_data.get('price'),
                        'image_url': product_data.get('image_url') or None,
                    }
                )
                
                if not created:
                    # Update quantity if item exists
                    item.quantity += serializer.validated_data['quantity']
                    item.save()
                
                # Update cart timestamp
                cart.updated_at = timezone.now()
                cart.save()
            
            # Return updated cart
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, cart_id=None):
        """Clear cart"""
        # Get cart
        if cart_id:
            cart = get_object_or_404(Cart, id=cart_id)
        elif request.user.is_authenticated:
            cart = get_object_or_404(Cart, customer_id=request.user.id)
        else:
            return Response(
                {"error": "Cart ID required for guest users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete all items
        cart.items.all().delete()
        
        # Update cart timestamp
        cart.updated_at = timezone.now()
        cart.save()
        
        # Return empty cart
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def _get_product_data(self, product_id, product_type):
        try:
            # Convert to string format if it's a UUID object
            product_id_str = str(product_id)
            
            url = f"{settings.MICROSERVICE_URLS['PRODUCT_SERVICE']}/{product_type}s/{product_id_str}/"
            response = requests.get(url)
            
            if response.status_code == 200:
                return response.json()
                
            # If standard UUID string didn't work, try with the Base64 format
            if response.status_code == 404:
                try:
                    # Format as Base64 if it's a UUID object
                    if isinstance(product_id, uuid.UUID):
                        base64_id = base64.b64encode(product_id.bytes).decode('ascii')
                        url = f"{settings.MICROSERVICE_URLS['PRODUCT_SERVICE']}/{product_type}s/{base64_id}/"
                        response = requests.get(url)
                        if response.status_code == 200:
                            return response.json()
                except:
                    pass
            
            return None
        except requests.RequestException:
            # In a real app, log this error
            return None
    
    def _clean_stale_items(self, cart):
        """Clean up expired items (optional)"""
        # This is a simple placeholder for more complex logic
        # You might want to periodically clean expired cart items
        pass

class CartItemView(APIView):
    def put(self, request, cart_id, item_id):
        """Update item quantity"""
        # Get cart and item
        cart = get_object_or_404(Cart, id=cart_id)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        # Validate input
        serializer = UpdateCartItemSerializer(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']
            
            if quantity > 0:
                # Update quantity
                item.quantity = quantity
                item.save()
            else:
                # Remove item
                item.delete()
            
            # Update cart timestamp
            cart.updated_at = timezone.now()
            cart.save()
            
            # Return updated cart
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, cart_id, item_id):
        """Remove item from cart"""
        # Get cart and item
        cart = get_object_or_404(Cart, id=cart_id)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        # Delete item
        item.delete()
        
        # Update cart timestamp
        cart.updated_at = timezone.now()
        cart.save()
        
        # Return updated cart
        serializer = CartSerializer(cart)
        return Response(serializer.data)

@api_view(['POST'])
def merge_carts(request):
    """Merge two carts"""
    serializer = CartMergeSerializer(data=request.data)
    if serializer.is_valid():
        source_cart_id = serializer.validated_data['source_cart_id']
        destination_cart_id = serializer.validated_data['destination_cart_id']
        
        try:
            source_cart = Cart.objects.get(id=source_cart_id)
            destination_cart = Cart.objects.get(id=destination_cart_id)
            
            with transaction.atomic():
                # Transfer items
                for item in source_cart.items.all():
                    # Check if item exists in destination cart
                    existing_item = destination_cart.items.filter(
                        product_id=item.product_id,
                        product_type=item.product_type
                    ).first()
                    
                    if existing_item:
                        # Update quantity if item exists
                        existing_item.quantity += item.quantity
                        existing_item.save()
                    else:
                        # Create new item in destination cart
                        item.pk = None  # Create new instance
                        item.id = uuid.uuid4()
                        item.cart = destination_cart
                        item.save()
                
                # Clear source cart
                source_cart.items.all().delete()
                
                # Update cart timestamps
                destination_cart.updated_at = timezone.now()
                destination_cart.save()
            
            # Return merged cart
            serializer = CartSerializer(destination_cart)
            return Response(serializer.data)
            
        except Cart.DoesNotExist:
            return Response(
                {"error": "One or both carts not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)