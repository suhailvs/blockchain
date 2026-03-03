from django.db import models
from crypto.models import Event
# Create your models here.
class EventVote(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    node_id = models.CharField(max_length=100)
    signature = models.TextField()
    approved = models.BooleanField()

class Node(models.Model):
    node_id = models.CharField(max_length=100, unique=True)
    public_key = models.TextField()
    url = models.URLField()
    def __str__(self):
        return self.node_id