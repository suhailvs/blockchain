from django.urls import include, path

from .views import submit_event, get_events_after,validate_event

urlpatterns = [
    path("events/<int:timestamp>/", get_events_after),
    path("submit/", submit_event),
    path("validate/", validate_event),
]