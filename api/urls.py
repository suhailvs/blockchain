from django.urls import path
from .views import EventSubmissionView, get_events_after,validate_event,finalize_event

urlpatterns = [
    path("events/", get_events_after),
    path("submit/", EventSubmissionView.as_view()),
    path("validate/", validate_event),
    path("finalize-event/", finalize_event),    
]