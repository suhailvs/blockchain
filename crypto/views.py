from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import EventProcessor,broadcast_event
from .models import Event
from consensus.utils import sign_vote

import uuid
@api_view(["POST"])
def submit_event(request):
    try:
        event = EventProcessor.process_event(request.data,str(uuid.uuid4()))
        broadcast_event(event)
        return Response({"event_id": str(event.id)})
    except Exception as e:
        return Response({"error": str(e)})

@api_view(["POST"])
def validate_event(request):
    resp = {"approved": False,"signature": sign_vote(request.data["hash"])}
    try:
        event = EventProcessor.process_event(request.data,request.data['event_id'])
        resp['approved']=True
    except Exception as e:
        resp['error']=str(e)
    return Response(resp)

@api_view(["GET"])
def get_events_after(request, timestamp):
    events = Event.objects.filter(timestamp__gt=timestamp)
    return Response([
        {
            "event_type": e.event_type,
            "payload": e.payload,
            "public_key": e.public_key,
            "signature": e.signature,
            "timestamp": e.timestamp
        }
        for e in events
    ])