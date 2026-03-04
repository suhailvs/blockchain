import requests
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import verify_and_add_event, count_valid_finalize_signatures
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
def sync_events(request):
    # Synchronize missing confirmed events from peers.
    events_synced = 0
    for peer in get_peers():
        last_event = Event.objects.filter(
            status="CONFIRMED"
        ).order_by("-height").first()
        print('Last Event Hash:',last_event.hash)
        try:
            response = requests.get(
                f"{peer.url}/api/events/",
                params={"after_hash": last_event.hash},
                timeout=5
            )
            if response.status_code != 200:
                continue
            remote_events = response.json().get("events", [])
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
    return Response({"status": "success","events_synced":events_synced})

@api_view(["POST"])
def finalize_event(request):
    event_id = request.data["event_id"]
    event_hash = request.data["event_hash"]
    signature_list = request.data["signature_list"]
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({"error": "Event not found"}, status=404)
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
