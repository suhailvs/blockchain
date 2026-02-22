import uuid
from django.db import models

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    public_key = models.TextField()
    signature = models.TextField()
    timestamp = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
        ]

class Identity(models.Model):
    public_key = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    nonce = models.BigIntegerField(default=0)  # Prevent replay attacks
    def __str__(self):
        return f'{self.id}, Nonce-{self.nonce}'

class Profile(models.Model):
    identity = models.ForeignKey(Identity,on_delete=models.CASCADE)
    image_hash = models.CharField(max_length=200)