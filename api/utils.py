import json
import hashlib
import requests
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from django.db import transaction
from django.conf import settings

from .models import Event, Identity,Node, Profile, ErrorLog

def get_peers():
    return Node.objects.exclude(node_id=settings.LOCAL_NODE_ID)

def apply_event(event):
    if event.event_type == "update_profile_image":
        identity= Identity.objects.get(public_key=event.public_key)
        profile, created = Profile.objects.get_or_create(identity=identity)
        profile.image_hash = event.payload["image_hash"]
        profile.save()
    elif event.event_type == "TRANSFER":
        # sender = event.payload["sender"]
        # receiver = event.payload["receiver"]
        # amount = event.payload["amount"]
        print('transfer')

def confirm_event(event):
    if Event.objects.filter(height=event.height, status="CONFIRMED").exists():
        # reject_this_event
        event.status = "REJECTED"
    else:
        event.status = "CONFIRMED"
    event.save()
    apply_event(event)

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

def generate_signature(message):
    private_key = SigningKey(settings.NODE_PRIVATE_KEY, encoder=HexEncoder)
    signed = private_key.sign(message.encode())
    return signed.signature.hex()

def verify_signature(public_key_hex, signature_hex, payload):
    try:
        public_key = VerifyKey(public_key_hex,encoder=HexEncoder)
        if isinstance(payload, str):
            message = payload
        else:
            message = json.dumps(payload, sort_keys=True)
        public_key.verify(message.encode(), bytes.fromhex(signature_hex))
        return True
    except Exception as e:
        print('='*50)
        print(e)
        print('-'*50)
        print('public_key_hex:',public_key_hex)
        print('signature_hex:',signature_hex)
        print('Payload:',payload)
        print('='*50)
        return False

def count_valid_finalize_signatures(event_hash, signature_list):
    valid_signatures = 0
    in_valid_signatures = 0
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
        else:
            in_valid_signatures += 1
    print('VALID SIGNATURES:',valid_signatures,', INVALID SIGNATURES:',in_valid_signatures)
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
            # TODO: While sync blockchain, for old events there may be less total nodes
            # ie new nodes might be added in future            
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
                "signature": generate_signature(f"FINALIZE:{event_hash}"),
            }],
            status=new_status,
        )

        if is_sync_blockchain:
            apply_event(event)
        
        # Update nonce
        identity.nonce = max(identity.nonce, nonce)
        identity.save()
        return event

def sync_events():
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
                    ErrorLog.objects.create(text=f"Error while syncing peer {peer.url}\n\nStatus Code: {response.status_code}")
                    break
                remote_events = response.json().get("events", [])
                if not remote_events:
                    # sync completed
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
                ErrorLog.objects.create(text=f'Error syncing from peer {peer.url}/api/events/\n\n{e}')
                break
    return events_synced