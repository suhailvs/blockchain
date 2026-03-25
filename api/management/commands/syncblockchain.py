from django.core.management.base import BaseCommand
from api.utils import sync_transactions

class Command(BaseCommand):
    help = "Synchronize missing confirmed transactions from peers."

    def handle(self, *args, **options):
        txns_synced = sync_transactions()
        self.stdout.write(
            self.style.SUCCESS(f'Transactions synced:{txns_synced}')
        )
        
        
