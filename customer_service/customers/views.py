from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Customer, Address
from .serializers import CustomerSerializer, AddressSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    
    # POST /api/customers/ - Create a new customer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"message": "Customer created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # POST /api/customers/{id}/add_address/ - Add address to a customer
    @action(detail=True, methods=['post'])
    def add_address(self, request, pk=None):
        customer = self.get_object()
        data = request.data
        data['customer'] = customer.id
        
        serializer = AddressSerializer(data=data)
        if serializer.is_valid():
            serializer.save(customer=customer)
            return Response(
                {"message": "Address added successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    
    # POST /api/addresses/ - Create a new address
    def create(self, request, *args, **kwargs):
        try:
            customer_id = request.data.get('customer_id')
            customer = Customer.objects.get(id=customer_id)
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(customer=customer)
                return Response(
                    {"message": "Address created successfully", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Customer.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )