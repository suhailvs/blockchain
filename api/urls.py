from django.urls import path
from .views import submit_event, get_events_after,validate_event,sync_events,finalize_event

urlpatterns = [
    path("sync/",sync_events),
    path("events/", get_events_after),
    path("submit/", submit_event),
    path("validate/", validate_event),
    path("finalize-event/", finalize_event),    
]