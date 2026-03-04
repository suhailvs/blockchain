from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import verify_and_add_event, count_valid_finalize_signatures
from .models import Event,Node
from .consensus import broadcast_event,sign_vote,sync_blockchain,confirm_event

import uuid
@api_view(["POST"])
def submit_event(request):
    try:
        event = verify_and_add_event(request.data,str(uuid.uuid4()))
        broadcast_event(event)
        return Response({"event_id": str(event.id)})
    except Exception as e:
        return Response({"error": str(e)})

@api_view(["POST"])
def validate_event(request):
    try:
        verify_and_add_event(request.data,request.data['event_id'])
        return Response({"approved": True,"signature": sign_vote(request.data["hash"])})
    
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
    sync_blockchain()
    return Response({"status": "success"})

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
