from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, ClothingViewSet, MobileViewSet, ProductImageViewSet, ProductSearchView

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'clothing', ClothingViewSet)
router.register(r'mobiles', MobileViewSet)
router.register(r'images', ProductImageViewSet)
router.register(r'search', ProductSearchView, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]