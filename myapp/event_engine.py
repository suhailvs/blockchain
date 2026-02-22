from django.db import transaction
from .models import Event, Identity
from .crypto import verify_signature
from .state_handlers import apply_event
class EventProcessor:

    @staticmethod
    @transaction.atomic
    def process_event(event_data):

        public_key = event_data["public_key"]
        signature = event_data["signature"]
        payload = event_data["payload"]
        timestamp = event_data["timestamp"]
        event_type = event_data["event_type"]
        nonce = payload.get("nonce")

        # 1️⃣ Verify identity exists
        identity = Identity.objects.select_for_update().get(public_key=public_key)

        # 2️⃣ Prevent replay attack
        if nonce <= identity.nonce:
            raise Exception("Replay attack detected")

        # 3️⃣ Verify signature
        if not verify_signature(public_key, signature, payload):
            raise Exception("Invalid signature")

        # 4️⃣ Store immutable event
        event = Event.objects.create(
            event_type=event_type,
            payload=payload,
            public_key=public_key,
            signature=signature,
            timestamp=timestamp
        )

        # 5️⃣ Apply state change
        EventProcessor.apply_event(event)

        # 6️⃣ Update nonce
        identity.nonce = nonce
        identity.save()

        return event

EventProcessor.apply_event = staticmethod(apply_event)