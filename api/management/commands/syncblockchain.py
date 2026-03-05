from django.core.management.base import BaseCommand
from api.utils import sync_events

class Command(BaseCommand):
    help = "Synchronize missing confirmed events from peers."

    def handle(self, *args, **options):
        events_synced = sync_events()
        self.stdout.write(
            self.style.SUCCESS(f'Events synced:{events_synced}')
        )
        
        