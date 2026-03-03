import requests
from .models import Node, EventVote
from django.conf import settings
from .models import Identity,Profile, Event

def get_peers():
    return Node.objects.exclude(node_id=settings.LOCAL_NODE_ID)

def apply_event(event):
    if event.event_type == "update_profile_image":
        identity= Identity.objects.get(public_key=event.public_key)
        profile, created = Profile.objects.get_or_create(identity=identity)
        profile.image_hash = event.payload["image_hash"]
        profile.save()



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

def broadcast_finalization(event):
    data = {
        "event_id": str(event.id),
        "event_hash": event.hash,
        "signature_list":[
            {
                "public_key":Node.objects.get(node_id=v.node_id).public_key,
                "signature":v.signature
            } for v in event.eventvote_set.all()
        ]
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
            print('Broadcast error.',e)
            continue
def confirm_event(event):
    from .utils import calculate_event_hash
    last_event = Event.objects.filter(
        status="CONFIRMED"
    ).order_by("-height").first()
    new_height = last_event.height + 1 if last_event else 0
    event_data = {"event_type":event.event_type,"payload":event.payload,
        "public_key":event.public_key, "previous_hash":event.previous_hash}
    event_hash = calculate_event_hash(event.id,event_data,new_height)

    event.hash = event_hash
    event.height = new_height
    event.status = "CONFIRMED"
    event.save()
    apply_event(event)

def check_majority(event):
    if event.status == "CONFIRMED":
        return
    approvals = EventVote.objects.filter(
        event=event,
        approved=True
    ).count()
    total_nodes = Node.objects.count()
    if approvals > total_nodes / 2:
        confirm_event(event)
        broadcast_finalization(event)
    


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
    from .utils import verify_and_add_event,create_genesis_event
    """
    Synchronize missing confirmed events from peers.
    """
    last_event = Event.objects.filter(
        status="CONFIRMED"
    ).order_by("-height").first()

    # if not last_event:
    #     last_event=create_genesis_event()
    after_hash = last_event.hash

    # Ask each peer
    events_synced = 0
    for peer in get_peers():
        try:
            response = requests.get(
                f"{peer.url}/api/events/",
                params={"after_hash": after_hash},
                timeout=5
            )
            if response.status_code != 200:
                continue

            remote_events = response.json().get("events", [])
            # Process received events
            for event_data in remote_events:
                if not verify_and_add_event(
                    event_data,
                    event_data['id'],
                    is_sync_blockchain=True,
                ):
                    break  # stop if chain breaks
                else:events_synced+=1

        except requests.RequestException:
            print('peer error:',peer.url)
            continue
    print('Events synced:',events_synced)
