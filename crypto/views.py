from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import verify_and_add_event,broadcast_event
from .models import Event
from consensus.utils import sign_vote,sync_blockchain

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
    resp = {"approved": False,"signature": sign_vote(request.data["hash"])}
    try:
        event = verify_and_add_event(request.data,request.data['event_id'])
        resp['approved']=True
    except Exception as e:
        resp['error']=str(e)
    return Response(resp)

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
        timestamp__gt=last_event.timestamp,
        status="CONFIRMED"
    ).order_by("timestamp")
    data = [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "payload": e.payload,
            "public_key": e.public_key,
            "signature": e.signature,
            "timestamp": e.timestamp,
            "previous_hash": e.previous_hash,
            "hash": e.hash,
        }
        for e in events
    ]
    return Response({"events": data})

@api_view(["GET"])
def sync_events(request):
    sync_blockchain()
    return Response({"status": "success"})