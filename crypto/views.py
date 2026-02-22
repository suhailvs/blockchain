from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import EventProcessor
from .models import Event
@api_view(["POST"])
def submit_event(request):
    try:
        event = EventProcessor.process_event(request.data)
        return Response({"status": "accepted", "event_id": str(event.id)})
    except Exception as e:
        return Response({"error": str(e)}, status=400)

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