import uuid,json
from django.db import models

class Event(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('CONFIRMED', 'CONFIRMED'),
        ('REJECTED','REJECTED')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    height = models.IntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    public_key = models.TextField()
    signature = models.TextField()
    hash = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64, null=True, blank=True)
    votes = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, default="PENDING",choices=STATUS_CHOICES)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["height"],
                condition=models.Q(status="CONFIRMED"),
                name="unique_confirmed_height"
            )]
    def __str__(self):
        return f'{self.status}:{str(self.id)[:5]}... {json.dumps(self.payload)}'

class Identity(models.Model):
    public_key = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    nonce = models.BigIntegerField(default=0)  # Prevent replay attacks
    def __str__(self):
        return f'{self.id}, Nonce-{self.nonce}'

class Profile(models.Model):
    identity = models.ForeignKey(Identity,on_delete=models.CASCADE)
    image_hash = models.CharField(max_length=200)
    def __str__(self):
        return f'{self.identity.id}:{self.image_hash[:10]}...'

class KeyPair(models.Model):
    # this table need to delete, only for testing purpose
    public_key = models.TextField(unique=True)
    private_key = models.TextField(unique=True)
    note = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f'{self.note}:{self.public_key[:5]}...'


class Node(models.Model):
    node_id = models.CharField(max_length=100, unique=True)
    public_key = models.TextField()
    url = models.URLField()
    def __str__(self):
        return self.node_id
