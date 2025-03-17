from django.core.management.base import BaseCommand
from django.utils import timezone
from carts.models import Cart

class Command(BaseCommand):
    help = 'Clean up expired cart data from database'

    def handle(self, *args, **options):
        # Get expired carts
        expired_carts = Cart.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = expired_carts.count()
        expired_carts.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully cleaned up {count} expired carts'))