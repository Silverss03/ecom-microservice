import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Payment, PaymentHistory, PaymentStatus
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, 
    ProcessPaymentSerializer, RefundPaymentSerializer
)
from .gateways import get_payment_gateway

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    @action(detail=False, methods=['post'])
    def process(self, request):
        """Process a pending payment"""
        serializer = ProcessPaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            payment = get_object_or_404(Payment, id=payment_id)
            
            # Skip processing if already processed
            if payment.status not in [PaymentStatus.PENDING, PaymentStatus.FAILED]:
                return Response({
                    'success': False,
                    'message': f'Payment cannot be processed (current status: {payment.status})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update payment status
            payment.status = PaymentStatus.PROCESSING
            payment.save()
            
            # Create history record
            PaymentHistory.objects.create(
                payment=payment,
                status=PaymentStatus.PROCESSING,
                notes="Payment processing started"
            )
            
            # Get payment gateway
            gateway = get_payment_gateway()
            
            # Process payment
            result = gateway.process_payment(
                amount=payment.amount,
                currency=payment.currency,
                payment_details=payment.payment_details
            )
            
            if result['success']:
                # Update payment with transaction ID and status
                payment.transaction_id = result['transaction_id']
                payment.status = PaymentStatus.COMPLETED
                payment.save()
                
                # Create history record
                PaymentHistory.objects.create(
                    payment=payment,
                    status=PaymentStatus.COMPLETED,
                    notes=f"Payment completed: {result['message']}"
                )
                
                # Notify order service
                try:
                    self._notify_order_service(payment)
                except requests.RequestException:
                    # Log error but continue (payment still successful)
                    pass
                
                return Response({
                    'success': True,
                    'payment_id': payment.id,
                    'transaction_id': payment.transaction_id,
                    'status': payment.status,
                    'message': result['message']
                })
            else:
                # Update payment status
                payment.status = PaymentStatus.FAILED
                payment.save()
                
                # Create history record
                PaymentHistory.objects.create(
                    payment=payment,
                    status=PaymentStatus.FAILED,
                    notes=f"Payment failed: {result['message']}"
                )
                
                return Response({
                    'success': False,
                    'payment_id': payment.id,
                    'status': payment.status,
                    'message': result['message'],
                    'error_code': result.get('error_code')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def refund(self, request):
        """Refund a completed payment"""
        serializer = RefundPaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            payment = get_object_or_404(Payment, id=payment_id)
            
            # Validate payment can be refunded
            if payment.status != PaymentStatus.COMPLETED:
                return Response({
                    'success': False,
                    'message': f'Payment cannot be refunded (current status: {payment.status})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get refund amount (default to full payment)
            refund_amount = serializer.validated_data.get('amount', payment.amount)
            
            # Get payment gateway
            gateway = get_payment_gateway()
            
            # Process refund
            result = gateway.refund_payment(
                transaction_id=payment.transaction_id,
                amount=refund_amount
            )
            
            if result['success']:
                # Update payment status
                payment.status = PaymentStatus.REFUNDED
                payment.save()
                
                # Create history record
                reason = serializer.validated_data.get('reason', 'No reason provided')
                PaymentHistory.objects.create(
                    payment=payment,
                    status=PaymentStatus.REFUNDED,
                    notes=f"Payment refunded: {reason}"
                )
                
                # Notify order service
                try:
                    self._notify_order_service(payment)
                except requests.RequestException:
                    # Log error but continue (refund still successful)
                    pass
                
                return Response({
                    'success': True,
                    'payment_id': payment.id,
                    'refund_id': result.get('refund_id'),
                    'status': payment.status,
                    'message': result['message']
                })
            else:
                # Create history record for failed refund attempt
                reason = serializer.validated_data.get('reason', 'No reason provided')
                PaymentHistory.objects.create(
                    payment=payment,
                    status=payment.status,  # Status hasn't changed
                    notes=f"Refund failed: {result['message']} (Reason: {reason})"
                )
                
                return Response({
                    'success': False,
                    'payment_id': payment.id,
                    'status': payment.status,
                    'message': result['message'],
                    'error_code': result.get('error_code')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get payment history"""
        payment = self.get_object()
        from .serializers import PaymentHistorySerializer
        history = payment.history.all()
        serializer = PaymentHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    def _notify_order_service(self, payment):
        """Notify order service about payment status changes"""
        url = f"{settings.MICROSERVICE_URLS['ORDER_SERVICE']}/orders/{payment.order_id}/update_payment/"
        
        data = {
            'status': payment.status,
            'transaction_id': payment.transaction_id,
            'payment_id': str(payment.id)
        }
        
        response = requests.post(url, json=data)
        return response.status_code == 200