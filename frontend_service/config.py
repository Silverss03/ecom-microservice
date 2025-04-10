import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development')
    
    # Microservice URLs
    PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL')
    CART_SERVICE_URL = os.environ.get('CART_SERVICE_URL')
    ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL')
    PAYMENT_SERVICE_URL = os.environ.get('PAYMENT_SERVICE_URL')
    SHIPMENT_SERVICE_URL = os.environ.get('SHIPMENT_SERVICE_URL')