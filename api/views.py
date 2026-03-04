import requests
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import verify_and_add_event, count_valid_finalize_signatures,sync_events
from .models import Event,Node
from .consensus import sign_vote,confirm_event,get_peers,check_majority


@api_view(["POST"])
def submit_event(request):
    try:
        event = verify_and_add_event(request.data,str(uuid.uuid4()))
        # broadcast_event
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
        return Response({"event_id": str(event.id)})
    except Exception as e:
        return Response({"error": str(e)})

@api_view(["POST"])
def validate_event(request):
    try:
        event = verify_and_add_event(request.data,request.data['event_id'])
        return Response({"approved": True,"signature": sign_vote(event.hash)})
    
    except Exception as e:
        return Response({"approved": False,"error":str(e)})

@api_view(["GET"])
def get_events_after(request):
    after_hash = request.GET.get("after_hash")
    if not after_hash:
        return Response({"error": "after_hash required"}, status=400)
    try:
        last_event = Event.objects.get(hash=after_hash)
    except Event.DoesNotExist:
        return Response({"error": "hash not found"}, status=404)
    events = Event.objects.filter(
        height__gt=last_event.height,
        status="CONFIRMED"
    ).order_by("height")
    data = [
        {
            "id": str(e.id),
            "height":e.height,
            "event_type": e.event_type,
            "payload": e.payload,
            "public_key": e.public_key,
            "signature": e.signature,
            "previous_hash": e.previous_hash,
            "hash": e.hash,
            "votes": e.votes,
        }
        for e in events
    ]
    return Response({"events": data})

@api_view(["GET"])
def sync(request):
    # Synchronize missing confirmed events from peers.
    events_synced = sync_events()
    print('Events synced:',events_synced)
    return Response({"events_synced":events_synced})

@api_view(["POST"])
def finalize_event(request):
    event_id = request.data["event_id"]
    event_hash = request.data["event_hash"]
    signature_list = request.data["signature_list"]
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # since we call finalize_event before all peers events update, we get error Event matching query does not exist.
        # TODO: don't know wheter to return 404 or do a sync_events function
        # return Response({"error": "Event not found"}, status=404)
        print('Event not found. So sync events')
        sync_events()
        return Response({"status": Event.objects.get(id=event_id).status})
        
    if event.hash != event_hash:
        return Response({"error": "Hash mismatch"}, status=400)
    valid_signatures = count_valid_finalize_signatures(event_hash, signature_list)

    if valid_signatures > Node.objects.count() / 2:
        event.votes = signature_list
        event.save(update_fields=["votes"])
        if event.status != "CONFIRMED":
            confirm_event(event)
        return Response({"status": "CONFIRMED"})

    return Response({"status": "PENDING", "valid_signatures": valid_signatures}, status=202)
