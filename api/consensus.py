import requests
from django.conf import settings
from .models import Node, Identity, Profile, Event

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

def broadcast_event(event):
    event_data = {
        "event_id": str(event.id),
        "event_type": event.event_type,
        "payload": event.payload,
        "public_key": event.public_key,
        "signature": event.signature,
        "hash": event.hash,
        "previous_hash": event.previous_hash,
    }
    for peer in get_peers():
        try:
            response = requests.post(
                f"{peer.url}/api/validate/",
                json=event_data,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("approved") and data.get("signature"):
                    # Keep one vote per validator public key.
                    votes = [v for v in event.votes if v.get("public_key") != peer.public_key]
                    votes.append({
                        "public_key": peer.public_key,
                        "signature": data["signature"],
                    })
                    event.votes = votes
                    event.save(update_fields=["votes"])
                check_majority(event)
        except requests.RequestException:
            print('Broadcast error.')
            continue

def broadcast_finalization(event):
    data = {
        "event_id": str(event.id),
        "event_hash": event.hash,
        "signature_list": event.votes,
    }
    for peer in get_peers():
        try:
            response = requests.post(
                f"{peer.url}/api/finalize-event/",
                json=data,
                timeout=3
            )
            print(peer.url,response.json())
        except Exception as e:
            print('Broadcast finalization error.',e)
            continue

def confirm_event(event):
    if Event.objects.filter(height=event.height, status="CONFIRMED").exists():
        # reject_this_event
        event.status = "REJECTED"
    else:
        event.status = "CONFIRMED"
    event.save()
    apply_event(event)

def check_majority(event):
    if event.status == "CONFIRMED":
        return
    from .utils import count_valid_finalize_signatures
    approvals = count_valid_finalize_signatures(event.hash, event.votes)
    total_nodes = Node.objects.count()
    if approvals > total_nodes / 2:
        confirm_event(event)
        broadcast_finalization(event)
    
def sign_vote(event_hash):
    from nacl.encoding import HexEncoder
    from nacl.signing import SigningKey
    message = f"FINALIZE:{event_hash}"
    private_key = SigningKey(settings.NODE_PRIVATE_KEY, encoder=HexEncoder)
    signed = private_key.sign(message.encode())
    return signed.signature.hex()

