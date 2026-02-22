from django.db import transaction
from .models import Event, Identity,Profile
def verify_signature(public_key_hex, signature_hex, payload_dict):
    import nacl.signing
    import nacl.encoding
    import json
    try:
        verify_key = nacl.signing.VerifyKey(
            public_key_hex,
            encoder=nacl.encoding.HexEncoder
        )

        message = json.dumps(payload_dict, sort_keys=True).encode()
        verify_key.verify(message, bytes.fromhex(signature_hex))
        return True
    except Exception:
        return False
def apply_event(event):
    if event.event_type == "update_profile_image":
        identity= Identity.objects.get(public_key=event.public_key)
        profile, created = Profile.objects.get_or_create(identity=identity)
        profile.image_hash = event.payload["image_hash"]
        profile.save()

class EventProcessor:

    @staticmethod
    @transaction.atomic
    def process_event(event_data):
        import time

        public_key = event_data["public_key"]
        signature = event_data["signature"]
        payload = event_data["payload"]
        timestamp = event_data["timestamp"]
        event_type = event_data["event_type"]
        nonce = payload.get("nonce")
        if abs(time.time() - timestamp) > 300:  # if MAX_DRIFT of timestamp is greater than 5 minutes
            raise Exception("Timestamp out of range")
        
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