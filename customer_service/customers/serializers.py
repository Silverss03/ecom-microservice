from rest_framework import serializers
from .models import Customer, Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_type', 'street_address', 'city', 
                  'state', 'postal_code', 'country', 'is_default']

class CustomerSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'email', 
                  'phone', 'date_joined', 'is_active', 'addresses']