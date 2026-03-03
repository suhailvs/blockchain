import requests
from .models import Node, EventVote
from django.conf import settings
from crypto.models import Identity,Profile, Event

def apply_event(event):
    if event.event_type == "update_profile_image":
        identity= Identity.objects.get(public_key=event.public_key)
        profile, created = Profile.objects.get_or_create(identity=identity)
        profile.image_hash = event.payload["image_hash"]
        profile.save()



def broadcast_event(event):
    peers = Node.objects.exclude(id=settings.LOCAL_NODE_ID)
    event_data = {
        "event_id": str(event.id),
        "event_type": event.event_type,
        "payload": event.payload,
        "public_key": event.public_key,
        "signature": event.signature,
        "timestamp": event.timestamp,
        "hash": event.hash,
        "previous_hash": event.previous_hash,
    }
    for peer in peers:
        try:
            response = requests.post(
                f"{peer.url}/api/validate/",
                json=event_data,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()

                EventVote.objects.update_or_create(
                    event=event,
                    node_id=peer.node_id,
                    defaults={
                        "approved": data.get("approved", False),
                        "signature": data.get("signature", "")
                    }
                )

                # Check majority after each vote
                check_majority(event)
        except requests.RequestException:
            # Node unreachable → ignore for now
            continue

def check_majority(event):
    total_nodes = Node.objects.count()
    
    approvals = EventVote.objects.filter(
        event=event,
        approved=True
    ).count()
    
    if approvals > total_nodes / 2:
        event.status = "CONFIRMED"
        event.save()
        apply_event(event)


def sign_vote(event_hash, approved):
    import nacl.signing
    import nacl.encoding
    message = f"{event_hash}:{approved}".encode()

    private_key_hex = settings.NODE_PRIVATE_KEY
    private_key = nacl.signing.SigningKey(
        private_key_hex,
        encoder=nacl.encoding.HexEncoder
    )

    signature = private_key.sign(message)

    return signature.hex()



def sync_blockchain():
    from crypto.utils import verify_and_add_event,create_genesis_event
    """
    Synchronize missing confirmed events from peers.
    """
    last_event = Event.objects.filter(
        status="CONFIRMED"
    ).order_by("-timestamp").first()

    if not last_event:
        last_event=create_genesis_event()
    after_hash = last_event.hash

    # 2️⃣ Ask each peer
    peers = Node.objects.exclude(node_id=settings.LOCAL_NODE_ID)

    for peer in peers:
        try:
            response = requests.get(
                f"{peer.url}/api/events/",
                params={"after_hash": after_hash},
                timeout=5
            )
            if response.status_code != 200:
                continue

            remote_events = response.json().get("events", [])
            print(remote_events,'after_hash:',after_hash)
            # 3️⃣ Process received events
            for event_data in remote_events:
                print(remote_events)
                if not verify_and_add_event(event_data):
                    break  # stop if chain breaks

        except requests.RequestException:
            print('peer error:',peer.url)
            continue