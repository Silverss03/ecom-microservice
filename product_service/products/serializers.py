from rest_framework import serializers
from .models import Book, Clothing, Mobile, ProductImage

class BookSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(default='book')
    
    class Meta:
        model = Book
        fields = '__all__'

class ClothingSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(default='clothing')
    
    class Meta:
        model = Clothing
        fields = '__all__'

class MobileSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(default='mobile')
    
    class Meta:
        model = Mobile
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'