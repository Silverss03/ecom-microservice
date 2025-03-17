import random
import uuid
import time
from datetime import datetime
from abc import ABC, abstractmethod
from django.conf import settings

class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def process_payment(self, amount, currency, payment_details):
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id, amount=None):
        pass
    
    @abstractmethod
    def check_payment_status(self, transaction_id):
        pass

class DemoPaymentGateway(PaymentGateway):
    """Demo payment gateway for testing"""
    
    def __init__(self):
        # Get configuration from settings
        config = settings.PAYMENT_GATEWAYS.get('DEMO_GATEWAY', {})
        self.api_key = config.get('API_KEY', 'fake_api_key')
        self.success_rate = config.get('SUCCESS_RATE', 0.9)
        
    def process_payment(self, amount, currency, payment_details):
        """Process a payment"""
        # Simulate processing time
        time.sleep(0.5)
        
        # Generate transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Simulate success/failure based on success rate
        is_successful = random.random() < self.success_rate
        
        # For cash on delivery, always succeed
        if payment_details.get('method') == 'CASH_ON_DELIVERY':
            is_successful = True
        
        # Simulate declined card for specific numbers
        card_number = payment_details.get('card_number', '')
        if card_number.endswith('0000'):
            is_successful = False
        
        if is_successful:
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': 'COMPLETED',
                'message': 'Payment processed successfully',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'status': 'FAILED',
                'message': 'Payment declined',
                'error_code': 'CARD_DECLINED',
                'timestamp': datetime.now().isoformat()
            }
    
    def refund_payment(self, transaction_id, amount=None):
        """Refund a payment"""
        # Simulate processing time
        time.sleep(0.5)
        
        # Generate refund ID
        refund_id = str(uuid.uuid4())
        
        # Simulate success/failure
        is_successful = random.random() < self.success_rate
        
        if is_successful:
            return {
                'success': True,
                'refund_id': refund_id,
                'transaction_id': transaction_id,
                'status': 'REFUNDED',
                'message': 'Refund processed successfully',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'transaction_id': transaction_id,
                'status': 'FAILED',
                'message': 'Refund could not be processed',
                'error_code': 'REFUND_FAILED',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_payment_status(self, transaction_id):
        """Check status of a payment"""
        # Simulate processing time
        time.sleep(0.2)
        
        # For demo purposes, most transactions are completed
        status = random.choices(
            ['COMPLETED', 'PROCESSING', 'FAILED'], 
            weights=[0.9, 0.05, 0.05], 
            k=1
        )[0]
        
        return {
            'transaction_id': transaction_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

# Factory to get the configured payment gateway
def get_payment_gateway():
    """Return the default payment gateway"""
    return DemoPaymentGateway()