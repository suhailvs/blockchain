from django.db import transaction
from .models import Event, Identity,Profile,EventVote
from .consensus import sign_vote
from django.conf import settings
import json
import hashlib

def calculate_event_hash(event_id,event):
    data = json.dumps({
        "id": str(event_id),
        "event_type": event['event_type'],
        "payload": event['payload'],
        "timestamp": event['timestamp'],
        "public_key": event['public_key'],
        "previous_hash": event['previous_hash'],
    }, sort_keys=True)
    
    return hashlib.sha256(data.encode()).hexdigest()


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


def create_genesis_event():
    # ./manage.py shell < t.py
    from .utils import calculate_event_hash
    if Event.objects.exists(): 
        print('Event Exists')
        return None
    GENESIS_ID=1
    event_data = {
        "id": str(GENESIS_ID),
        "event_type": "GENESIS",
        "payload": {"message": "Initial event"},
        "timestamp": 0,
        "public_key": "SYSTEM",
        "previous_hash": "0" * 64,
    }

    event_hash = calculate_event_hash(event_data['id'],event_data)
    print('Event Created')
    return Event.objects.create(
        id=GENESIS_ID,
        event_type="GENESIS",
        payload=event_data["payload"],
        public_key="SYSTEM",
        signature="GENESIS",
        timestamp=0,
        previous_hash="0" * 64,
        hash=event_hash,
        status="CONFIRMED"
    )

def verify_and_add_event(event_data, event_id, validate_timestamp=True, mark_confirmed=False):
    import time
    with transaction.atomic():
        public_key = event_data["public_key"]
        signature = event_data["signature"]
        payload = event_data["payload"]
        timestamp = int(event_data["timestamp"])
        event_type = event_data["event_type"]
        nonce = payload.get("nonce")
        # Enforce drift checks for live submissions, but allow historical sync imports.
        if validate_timestamp and abs(time.time() - timestamp) > 300:  # if MAX_DRIFT of timestamp is greater than 5 minutes
            raise Exception(f"Timestamp out of range, {int(time.time())}")
        
        # 1️⃣ Verify identity exists
        identity = Identity.objects.select_for_update().get(public_key=public_key)
        # 2️⃣ Prevent replay attack
        if nonce <= identity.nonce:
            raise Exception("Replay attack detected")

        # 3️⃣ Verify signature
        if not verify_signature(public_key, signature, payload):
            raise Exception("Invalid signature")
        last_event = Event.objects.filter(
            status="CONFIRMED"
        ).order_by("-timestamp").first()
        previous_hash = last_event.hash if last_event else "0" * 64
        event_hash = calculate_event_hash(event_id,event_data)

        if event_data["previous_hash"] != previous_hash:
            raise Exception("Previous Hash doesn't match")
        # 4️⃣ Store immutable event
        event = Event.objects.create(
            id=event_id,
            event_type=event_type,
            payload=payload,
            public_key=public_key,
            signature=signature,
            timestamp=timestamp,
            previous_hash=previous_hash,
            hash=event_hash,
            status="CONFIRMED" if mark_confirmed else "PENDING",
        )
        approved = True
        EventVote.objects.create(
            event=event,
            node_id=settings.LOCAL_NODE_ID,
            approved=approved,
            signature=sign_vote(event.hash,approved)
        )

        
        apply_event(event)
        # 6️⃣ Update nonce
        identity.nonce = nonce
        identity.save()

        return event