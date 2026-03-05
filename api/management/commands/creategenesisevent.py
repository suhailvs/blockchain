from django.core.management.base import BaseCommand
from api.models import Event
from api.utils import calculate_event_hash

class Command(BaseCommand):
    help = "Create Genesis Event."

    def handle(self, *args, **options):
        if Event.objects.filter(status="CONFIRMED").exists():
            self.stdout.write("Error: Event already exists")
            return 
        GENESIS_ID=1
        height = 0
        event_data = {
            "event_type": "GENESIS",
            "payload": {"message": "Initial event"},
            "public_key": "SYSTEM",
            "previous_hash": "0" * 64,
        }
        event_hash = calculate_event_hash(str(GENESIS_ID),event_data,height)
        Event.objects.create(
            id=GENESIS_ID,
            height=height,
            event_type=event_data['event_type'],
            payload=event_data["payload"],
            public_key=event_data['public_key'],
            signature="GENESIS",
            previous_hash=event_data['previous_hash'],
            hash=event_hash,
            status="CONFIRMED"
        )
        self.stdout.write(
            self.style.SUCCESS('GENESIS Event Created Successfully.')
        )