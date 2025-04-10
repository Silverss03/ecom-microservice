from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .services import RecommendationService

class RecommendationViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def similar_products(self, request):
        """Get products similar to a specified product based on sentiment"""
        product_id = request.query_params.get('product_id')
        limit = int(request.query_params.get('limit', 10))
        
        if not product_id:
            return Response({"error": "product_id parameter is required"}, status=400)
            
        recommendations = RecommendationService.get_similar_sentiment_products(product_id, limit)
        return Response(self._format_recommendations(recommendations))
    
    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """Get personalized recommendations for a user based on sentiment"""
        user_id = request.query_params.get('user_id')
        limit = int(request.query_params.get('limit', 10))
        
        if not user_id:
            return Response({"error": "user_id parameter is required"}, status=400)
            
        recommendations = RecommendationService.get_personalized_recommendations(user_id, limit)
        return Response(self._format_recommendations(recommendations))
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top rated products by sentiment score"""
        limit = int(request.query_params.get('limit', 10))
        recommendations = RecommendationService.get_top_rated_products(limit)
        return Response(self._format_recommendations(recommendations))
    
    def _format_recommendations(self, recommendations):
        """Format recommendation data for API response"""
        return [
            {
                'id': str(item['product'].id),
                'name': item['product'].name,
                'price': float(item['product'].price),
                'score': float(item['score']),
                'image_url': item['product'].image_url
            }
            for item in recommendations
        ]