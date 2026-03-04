import json
import hashlib
from django.db import transaction
from django.conf import settings

from .models import Event, Identity,Node
from .consensus import sign_vote, apply_event

def calculate_event_hash(event_id,event, height):
    data = json.dumps({
        "id": str(event_id),
        "event_type": event['event_type'],
        "payload": event['payload'],
        "height": height,
        "public_key": event['public_key'],
        "previous_hash": event['previous_hash'],
    }, sort_keys=True)
    
    return hashlib.sha256(data.encode()).hexdigest()


def verify_signature(public_key_hex, signature_hex, payload):
    from nacl.encoding import HexEncoder
    from nacl.signing import VerifyKey
    try:
        public_key = VerifyKey(public_key_hex,encoder=HexEncoder)
        if isinstance(payload, str):
            message = payload
        else:
            message = json.dumps(payload, sort_keys=True)
        public_key.verify(message.encode(), bytes.fromhex(signature_hex))
        return True
    except Exception as e:
        print(e)
        return False

def count_valid_finalize_signatures(event_hash, signature_list):
    valid_signatures = 0
    seen_keys = set()

    for item in signature_list:
        public_key = item.get("public_key")
        vote_signature = item.get("signature")

        if not public_key or not vote_signature:
            continue

        if public_key in seen_keys:
            continue

        if not Node.objects.filter(public_key=public_key).exists():
            continue

        if verify_signature(public_key, vote_signature, f"FINALIZE:{event_hash}"):
            valid_signatures += 1
            seen_keys.add(public_key)

    return valid_signatures
    

def verify_and_add_event(event_data, event_id, is_sync_blockchain=False):
    with transaction.atomic():
        public_key = event_data["public_key"]
        signature = event_data["signature"]
        payload = event_data["payload"]
        event_type = event_data["event_type"]
        previous_hash = event_data["previous_hash"]
        nonce = payload.get("nonce")
        # Verify identity exists
        identity = Identity.objects.select_for_update().get(public_key=public_key)
        # Prevent replay attack for live submissions.
        if not is_sync_blockchain and nonce <= identity.nonce:
            raise Exception(f"Replay attack detected. Nonce:{nonce}, Identity nonce:{identity.nonce}")
        # Verify signature
        signed_payload = {
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }        
        if not verify_signature(public_key, signature, signed_payload):
            raise Exception("Invalid signature")
        last_event = Event.objects.filter(
            status="CONFIRMED"
        ).order_by("-height").first()

        if event_data["previous_hash"] != last_event.hash:
            raise Exception("Previous Hash doesn't match")

        if is_sync_blockchain:
            signature_list = event_data.get("signature_list", event_data.get("votes", []))
            new_height = event_data["height"]
            expected_height = last_event.height + 1
            if new_height != expected_height:
                raise Exception("Invalid height during sync")

            expected_hash = calculate_event_hash(event_id, event_data, height=new_height)
            if event_data["hash"] != expected_hash:
                raise Exception("Invalid event hash during sync")

            event_hash = expected_hash
            valid_signatures = count_valid_finalize_signatures(event_hash, signature_list)

            if valid_signatures <= Node.objects.count() / 2:
                raise Exception("Insufficient valid EventVote signatures")
            new_status = "CONFIRMED"
        else:
            last_event = Event.objects.filter(
                status="CONFIRMED"
            ).order_by("-height").first()
            new_height = last_event.height + 1
            
            event_hash = calculate_event_hash(event_id,event_data,height=new_height)
            new_status = "PENDING"

        # Store immutable event
        event = Event.objects.create(
            id=event_id,
            height=new_height,
            event_type=event_type,
            payload=payload,
            public_key=public_key,
            signature=signature,
            previous_hash=previous_hash,
            hash=event_hash,
            votes=signature_list if is_sync_blockchain else [{
                "public_key": Node.objects.get(node_id=settings.LOCAL_NODE_ID).public_key,
                "signature": sign_vote(event_hash),
            }],
            status=new_status,
        )

        if is_sync_blockchain:
            apply_event(event)

        
        # Update nonce
        identity.nonce = max(identity.nonce, nonce)
        identity.save()

        return event
