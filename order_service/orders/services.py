import requests
from django.conf import settings

class ProductServiceClient:
    """Client for interacting with the Product Service API"""
    
    def __init__(self):
        self.base_url = settings.MICROSERVICE_URLS['PRODUCT_SERVICE']
    
    def get_product(self, product_type, product_id):
        url = f"{self.base_url}/{product_type}s/{product_id}/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            # Log error
            pass
        return None
    
    def update_stock(self, product_type, product_id, quantity):
        url = f"{self.base_url}/{product_type}s/{product_id}/update_stock/"
        try:
            response = requests.patch(url, json={"quantity_change": -quantity})
            return response.status_code == 200
        except requests.RequestException:
            # Log error
            return False

class CustomerServiceClient:
    """Client for interacting with the Customer Service API"""
    
    def __init__(self):
        self.base_url = settings.MICROSERVICE_URLS['CUSTOMER_SERVICE']
    
    def get_customer(self, customer_id):
        url = f"{self.base_url}/customers/{customer_id}/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            # Log error
            pass
        return None