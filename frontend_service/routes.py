import os
import requests
from flask import render_template, request, session, redirect, url_for
from app import app

# Use environment variables for service URLs
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL')

@app.route('/')
def home():
    """Homepage with recommendations"""
    # Fetch top-rated products
    top_rated_products = []
    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/recommendations/top_rated/")
        if response.status_code == 200:
            top_rated_products = response.json()
    except Exception as e:
        app.logger.error(f"Error fetching top rated products: {e}")
    
    # Fetch personalized recommendations if user is logged in
    personalized_recommendations = []
    user_id = session.get('user_id')
    if user_id:
        try:
            response = requests.get(
                f"{PRODUCT_SERVICE_URL}/recommendations/personalized/",
                params={"user_id": user_id}
            )
            if response.status_code == 200:
                personalized_recommendations = response.json()
        except Exception as e:
            app.logger.error(f"Error fetching personalized recommendations: {e}")
    
    return render_template(
        'pages/home.html',
        top_rated_products=top_rated_products,
        personalized_recommendations=personalized_recommendations,
        user_id=user_id
    )

@app.route('/products/<product_id>')
def product_detail(product_id):
    """Product detail page with similar product recommendations"""
    # Fetch product details
    product = None
    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}/")
        if response.status_code == 200:
            product = response.json()
        else:
            return redirect(url_for('home'))
    except Exception as e:
        app.logger.error(f"Error fetching product details: {e}")
        return redirect(url_for('home'))
    
    # Fetch similar products recommendations
    similar_products = []
    try:
        response = requests.get(
            f"{PRODUCT_SERVICE_URL}/recommendations/similar_products/",
            params={"product_id": product_id}
        )
        if response.status_code == 200:
            similar_products = response.json()
    except Exception as e:
        app.logger.error(f"Error fetching similar products: {e}")
    
    return render_template(
        'pages/product_detail.html',
        product=product,
        similar_products=similar_products
    )