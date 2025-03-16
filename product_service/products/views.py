from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Book, Clothing, Mobile, ProductImage
from .serializers import BookSerializer, ClothingSerializer, MobileSerializer, ProductImageSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all images for a specific book"""
        images = ProductImage.objects.filter(product_id=pk, product_type='book')
        serializer = ProductImageSerializer(images, many=True)
        return Response(serializer.data)

class ClothingViewSet(viewsets.ModelViewSet):
    queryset = Clothing.objects.all()
    serializer_class = ClothingSerializer
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all images for a specific clothing item"""
        images = ProductImage.objects.filter(product_id=pk, product_type='clothing')
        serializer = ProductImageSerializer(images, many=True)
        return Response(serializer.data)

class MobileViewSet(viewsets.ModelViewSet):
    queryset = Mobile.objects.all()
    serializer_class = MobileSerializer
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all images for a specific mobile item"""
        images = ProductImage.objects.filter(product_id=pk, product_type='mobile')
        serializer = ProductImageSerializer(images, many=True)
        return Response(serializer.data)

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

class ProductSearchView(viewsets.ViewSet):
    def list(self, request):
        """Search products across all categories"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        
        results = []
        
        if not category or category == 'book':
            books = Book.objects.filter(name__icontains=query, is_active=True)
            book_data = BookSerializer(books, many=True).data
            results.extend(book_data)
            
        if not category or category == 'clothing':
            clothes = Clothing.objects.filter(name__icontains=query, is_active=True)
            clothing_data = ClothingSerializer(clothes, many=True).data
            results.extend(clothing_data)
            
        if not category or category == 'mobile':
            mobiles = Mobile.objects.filter(name__icontains=query, is_active=True)
            mobile_data = MobileSerializer(mobiles, many=True).data
            results.extend(mobile_data)
            
        return Response(results)