import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import random

from .models import Shipment, ShipmentUpdate, ShipmentStatus
from .serializers import (
    ShipmentSerializer, ShipmentCreateSerializer, 
    UpdateShipmentStatusSerializer, ProcessShipmentSerializer, 
    DeliverShipmentSerializer, ShipmentUpdateSerializer
)

class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ShipmentCreateSerializer
        return ShipmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by order_id if provided
        order_id = self.request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by tracking_number if provided
        tracking_number = self.request.query_params.get('tracking_number')
        if tracking_number:
            queryset = queryset.filter(tracking_number=tracking_number)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a shipment"""
        shipment = self.get_object()
        
        serializer = UpdateShipmentStatusSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            location = serializer.validated_data.get('location', '')
            description = serializer.validated_data.get('description', '')
            
            # Update shipment status
            old_status = shipment.status
            shipment.status = new_status
            
            # Update shipping_date if status changes to IN_TRANSIT
            if new_status == ShipmentStatus.IN_TRANSIT and old_status != ShipmentStatus.IN_TRANSIT:
                shipment.shipping_date = timezone.now()
                # Recalculate estimated delivery based on new shipping date
                shipment.estimated_delivery = shipment._calculate_estimated_delivery()
            
            # Update actual_delivery if status changes to DELIVERED
            if new_status == ShipmentStatus.DELIVERED:
                shipment.actual_delivery = timezone.now()
            
            shipment.save()
            
            # Create status update record
            update = ShipmentUpdate.objects.create(
                shipment=shipment,
                status=new_status,
                location=location,
                description=description or f"Status changed from {old_status} to {new_status}"
            )
            
            # Notify order service about status change if needed
            try:
                if new_status in [ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED, 
                                 ShipmentStatus.RETURNED, ShipmentStatus.CANCELLED]:
                    self._notify_order_service(shipment)
            except requests.RequestException:
                # Log error but don't fail the request
                pass
            
            # Return updated shipment
            serializer = self.get_serializer(shipment)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def process(self, request):
        """Process a pending shipment (move to PROCESSING status)"""
        serializer = ProcessShipmentSerializer(data=request.data)
        if serializer.is_valid():
            shipment_id = serializer.validated_data['shipment_id']
            shipment = get_object_or_404(Shipment, id=shipment_id)
            
            if shipment.status != ShipmentStatus.PENDING:
                return Response({
                    'detail': f'Shipment cannot be processed (current status: {shipment.status})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update status to PROCESSING
            shipment.status = ShipmentStatus.PROCESSING
            shipment.save()
            
            # Create status update
            ShipmentUpdate.objects.create(
                shipment=shipment,
                status=ShipmentStatus.PROCESSING,
                description="Shipment processing has begun"
            )
            
            # Return updated shipment
            serializer = self.get_serializer(shipment)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def ship(self, request):
        """Mark a processed shipment as shipped (IN_TRANSIT)"""
        serializer = ProcessShipmentSerializer(data=request.data)
        if serializer.is_valid():
            shipment_id = serializer.validated_data['shipment_id']
            shipment = get_object_or_404(Shipment, id=shipment_id)
            
            if shipment.status != ShipmentStatus.PROCESSING and shipment.status != ShipmentStatus.READY_FOR_PICKUP:
                return Response({
                    'detail': f'Shipment cannot be shipped (current status: {shipment.status})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update status to IN_TRANSIT
            shipment.status = ShipmentStatus.IN_TRANSIT
            shipment.shipping_date = timezone.now()
            shipment.estimated_delivery = shipment._calculate_estimated_delivery()
            shipment.save()
            
            # Create status update
            ShipmentUpdate.objects.create(
                shipment=shipment,
                status=ShipmentStatus.IN_TRANSIT,
                description="Shipment has been picked up by the carrier"
            )
            
            # Notify order service
            try:
                self._notify_order_service(shipment)
            except requests.RequestException:
                # Log error but don't fail the request
                pass
            
            # Return updated shipment
            serializer = self.get_serializer(shipment)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def deliver(self, request):
        """Mark a shipment as delivered"""
        serializer = DeliverShipmentSerializer(data=request.data)
        if serializer.is_valid():
            shipment_id = serializer.validated_data['shipment_id']
            proof = serializer.validated_data.get('proof_of_delivery', '')
            shipment = get_object_or_404(Shipment, id=shipment_id)
            
            if shipment.status != ShipmentStatus.IN_TRANSIT and shipment.status != ShipmentStatus.OUT_FOR_DELIVERY:
                return Response({
                    'detail': f'Shipment cannot be delivered (current status: {shipment.status})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update status to DELIVERED
            shipment.status = ShipmentStatus.DELIVERED
            shipment.actual_delivery = timezone.now()
            shipment.save()
            
            # Create status update
            description = "Shipment has been delivered successfully"
            if proof:
                description += f" (Proof: {proof})"
                
            ShipmentUpdate.objects.create(
                shipment=shipment,
                status=ShipmentStatus.DELIVERED,
                description=description
            )
            
            # Notify order service
            try:
                self._notify_order_service(shipment)
            except requests.RequestException:
                # Log error but don't fail the request
                pass
            
            # Return updated shipment
            serializer = self.get_serializer(shipment)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Get tracking information for a shipment"""
        shipment = self.get_object()
        
        # Get shipment updates
        updates = shipment.updates.all()
        update_serializer = ShipmentUpdateSerializer(updates, many=True)
        
        # Add simulated updates if needed for demo purposes
        if len(updates) <= 2 and shipment.status not in [ShipmentStatus.PENDING, ShipmentStatus.CANCELLED]:
            simulated_updates = self._generate_simulated_updates(shipment)
            response_data = {
                'shipment': self.get_serializer(shipment).data,
                'updates': update_serializer.data + simulated_updates,
                'simulated': True
            }
        else:
            response_data = {
                'shipment': self.get_serializer(shipment).data,
                'updates': update_serializer.data,
                'simulated': False
            }
        
        return Response(response_data)
    
    def _notify_order_service(self, shipment):
        """Notify order service about shipment status changes"""
        url = f"{settings.MICROSERVICE_URLS['ORDER_SERVICE']}/orders/{shipment.order_id}/update_shipment/"
        
        data = {
            'status': shipment.status,
            'tracking_number': shipment.tracking_number,
            'shipment_id': str(shipment.id),
            'shipping_date': shipment.shipping_date.isoformat() if shipment.shipping_date else None,
            'estimated_delivery': shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
            'actual_delivery': shipment.actual_delivery.isoformat() if shipment.actual_delivery else None,
            'tracking_url': shipment.get_tracking_url()
        }
        
        response = requests.post(url, json=data)
        return response.status_code == 200
    
    def _generate_simulated_updates(self, shipment):
        """Generate simulated updates for demo purposes"""
        import random
        from datetime import timedelta
        
        # Define some locations for simulation
        sorting_centers = [
            "Main Distribution Center",
            "Regional Sorting Facility",
            "Local Dispatch Center"
        ]
        
        transit_locations = [
            "En route to next facility",
            "In transit",
            "Arrived at regional hub",
            "Departed from regional hub",
            "Arrived at local facility"
        ]
        
        if not shipment.shipping_date:
            return []
        
        updates = []
        current_time = shipment.shipping_date
        
        # Add sorting center update
        if shipment.status not in [ShipmentStatus.PENDING, ShipmentStatus.PROCESSING]:
            sorting_center = random.choice(sorting_centers)
            updates.append({
                'status': ShipmentStatus.PROCESSING,
                'timestamp': (current_time + timedelta(hours=random.randint(2, 8))).isoformat(),
                'location': sorting_center,
                'description': f"Shipment received at {sorting_center}"
            })
            
        # Add transit updates
        if shipment.status in [ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.DELIVERED]:
            num_updates = random.randint(1, 3)
            for i in range(num_updates):
                current_time += timedelta(hours=random.randint(8, 24))
                transit_location = random.choice(transit_locations)
                updates.append({
                    'status': ShipmentStatus.IN_TRANSIT,
                    'timestamp': current_time.isoformat(),
                    'location': f"Transit Location {i+1}",
                    'description': transit_location
                })
            
        # Add out for delivery update
        if shipment.status in [ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.DELIVERED]:
            current_time += timedelta(hours=random.randint(8, 24))
            updates.append({
                'status': ShipmentStatus.OUT_FOR_DELIVERY,
                'timestamp': current_time.isoformat(),
                'location': "Local Delivery Facility",
                'description': "Shipment out for delivery"
            })
            
        # Add delivery update
        if shipment.status == ShipmentStatus.DELIVERED and shipment.actual_delivery:
            updates.append({
                'status': ShipmentStatus.DELIVERED,
                'timestamp': shipment.actual_delivery.isoformat(),
                'location': "Delivery Address",
                'description': "Shipment delivered successfully"
            })
            
        # Sort updates by timestamp
        updates.sort(key=lambda x: x['timestamp'])
        return updates