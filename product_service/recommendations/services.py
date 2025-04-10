from products.models import Product, ProductSentiment
from django.db.models import Q, F, ExpressionWrapper, FloatField

class RecommendationService:
    @staticmethod
    def get_sentiment_based_recommendations(user_id=None, product_id=None, limit=10):
        """Get sentiment-based product recommendations"""
        if product_id:
            return RecommendationService.get_similar_sentiment_products(product_id, limit)
        elif user_id:
            return RecommendationService.get_personalized_recommendations(user_id, limit)
        else:
            return RecommendationService.get_top_rated_products(limit)
    
    @staticmethod
    def get_similar_sentiment_products(product_id, limit=10):
        """Find products with similar positive aspects"""
        try:
            # Get source product sentiment
            source_sentiment = ProductSentiment.objects.select_related('product').get(product_id=product_id)
            
            # Extract positive aspects from the source product
            positive_aspects = [a['aspect'] for a in source_sentiment.top_positive_aspects]
            
            if not positive_aspects:
                return RecommendationService.get_top_rated_products(limit)
            
            # Find products that share these positive aspects
            product_scores = {}
            
            for sentiment in ProductSentiment.objects.select_related('product').exclude(product_id=product_id):
                score = 0
                # Check each aspect in this product
                for aspect, data in sentiment.aspect_sentiment.items():
                    if aspect in positive_aspects and data['score'] > 0:
                        score += data['score'] * data['count']
                
                if score > 0:
                    product_scores[sentiment.product] = score
            
            # Sort by score and return top products
            sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            return [{'product': p[0], 'score': p[1]} for p in sorted_products]
            
        except ProductSentiment.DoesNotExist:
            return RecommendationService.get_top_rated_products(limit)
    
    @staticmethod
    def get_personalized_recommendations(user_id, limit=10):
        """Get personalized recommendations based on user's past reviews"""
        # Fetch aspects the user has positively commented on
        user_comments = Comment.objects.filter(user_id=user_id, sentiment_score__gt=0)
        
        if not user_comments.exists():
            return RecommendationService.get_top_rated_products(limit)
        
        # Collect aspects the user likes
        user_aspects = {}
        for comment in user_comments:
            for aspect in comment.sentiment_aspects:
                if aspect in user_aspects:
                    user_aspects[aspect] += comment.sentiment_score
                else:
                    user_aspects[aspect] = comment.sentiment_score
        
        # Sort aspects by sentiment score
        sorted_aspects = sorted(user_aspects.items(), key=lambda x: x[1], reverse=True)
        top_aspects = [a[0] for a in sorted_aspects[:10]]
        
        if not top_aspects:
            return RecommendationService.get_top_rated_products(limit)
        
        # Find products that have these aspects rated positively
        product_scores = {}
        
        for sentiment in ProductSentiment.objects.select_related('product'):
            score = 0
            for aspect, data in sentiment.aspect_sentiment.items():
                if aspect in top_aspects and data['score'] > 0:
                    score += data['score'] * data['count']
            
            if score > 0:
                product_scores[sentiment.product] = score
        
        # Filter out products the user has already reviewed
        reviewed_products = user_comments.values_list('entity_id', flat=True)
        product_scores = {p: s for p, s in product_scores.items() if str(p.id) not in reviewed_products}
        
        # Sort by score and return top products
        sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'product': p[0], 'score': p[1]} for p in sorted_products]
    
    @staticmethod
    def get_top_rated_products(limit=10):
        """Get products with highest sentiment scores"""
        top_products = (ProductSentiment.objects
                       .select_related('product')
                       .filter(review_count__gte=5)  # Only consider products with sufficient reviews
                       .order_by('-avg_sentiment_score')[:limit])
        
        return [{'product': s.product, 'score': s.avg_sentiment_score} for s in top_products]