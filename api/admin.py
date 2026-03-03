from django.contrib import admin
from .models import (EventVote, Node,Event, Identity, Profile,KeyPair)

admin.site.register(Event)
admin.site.register(Identity)
admin.site.register(Profile)
admin.site.register(KeyPair)

admin.site.register(EventVote)
admin.site.register(Node)