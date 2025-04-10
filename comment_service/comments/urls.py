from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet, CommentFlagViewSet

router = DefaultRouter()
router.register(r'comments', CommentViewSet)
router.register(r'flags', CommentFlagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]