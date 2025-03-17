from django.urls import path
from . import views

urlpatterns = [
    # Cart operations
    path('carts/<uuid:cart_id>/', views.CartView.as_view(), name='cart-detail'),
    path('carts/<uuid:cart_id>/items/<uuid:item_id>/', views.CartItemView.as_view(), name='cart-item-detail'),
    path('carts/merge/', views.merge_carts, name='merge-carts'),
    path('carts/', views.CartView.as_view(), name='user-cart'),  # For authenticated users
]