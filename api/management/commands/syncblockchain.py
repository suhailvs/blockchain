import requests
from django.core.management.base import BaseCommand
from api.models import Event
from api.utils import verify_and_add_event,get_peers

class Command(BaseCommand):
    help = "Synchronize missing confirmed events from peers."

    def handle(self, *args, **options):
        events_synced = 0
        for peer in get_peers():
            while True:
                # api/events/ only will give 100 events per request so need to run loop
                last_event = Event.objects.filter(
                    status="CONFIRMED"
                ).order_by("-height").first()
                try:
                    response = requests.get(
                        f"{peer.url}/api/events/",
                        params={"after_hash": last_event.hash},
                        timeout=5
                    )
                    if response.status_code != 200:
                        self.stdout.write(f"Error while syncing peer {peer.url}")
                        break
                    remote_events = response.json().get("events", [])
                    if not remote_events:
                        # sync completed
                        self.stdout.write(
                            self.style.SUCCESS(f'All events synced in peer {peer.url}')
                        )
                        break
                    for event_data in remote_events:
                        if not verify_and_add_event(
                            event_data,
                            event_data['id'],
                            is_sync_blockchain=True,
                        ):
                            break  # stop if chain breaks
                        else:events_synced+=1
                except Exception as e:
                    self.stdout.write(f"Error syncing from peer:{peer.url},{e}")
                    break
        self.stdout.write(
            self.style.SUCCESS(f'Events synced:{events_synced}')
        )
        
        