from django.core.management.base import BaseCommand
from comments.models import Comment
from comments.services import SentimentAnalysisService
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Analyze existing comments with CNN sentiment model'
    
    def handle(self, *args, **options):
        sentiment_service = SentimentAnalysisService()
        
        # Get comments without sentiment analysis
        comments = Comment.objects.filter(sentiment_score__isnull=True)
        total = comments.count()
        
        self.stdout.write(f"Analyzing {total} comments...")
        
        for i, comment in enumerate(comments):
            # Analyze comment text
            sentiment_data = sentiment_service.analyze_text(comment.content)
            
            # Update comment with sentiment data
            comment.sentiment_score = sentiment_data['normalized_score']
            comment.sentiment_aspects = sentiment_data['aspects']
            comment.save()
            
            # Notify product service if this is a product comment
            if comment.entity_type == 'product':
                try:
                    url = f"{settings.SERVICE_URLS['product_service']}/api/products/{comment.entity_id}/sentiment/"
                    data = {
                        'comment_id': str(comment.id),
                        'user_id': str(comment.user_id),
                        'rating': comment.rating,
                        'sentiment_score': sentiment_data['normalized_score'],
                        'sentiment_aspects': sentiment_data['aspects']
                    }
                    requests.post(url, json=data)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error notifying product service for comment {comment.id}: {e}"))
            
            # Show progress
            if (i + 1) % 100 == 0 or (i + 1) == total:
                self.stdout.write(f"Processed {i + 1}/{total} comments")
        
        self.stdout.write(self.style.SUCCESS('Successfully analyzed all comments'))