from django.urls import include, path

from .views import submit_event, get_events_after

urlpatterns = [
    path("events/<int:timestamp>/", get_events_after),
    path("submit/", submit_event),
]