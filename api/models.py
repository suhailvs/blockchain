import uuid,json
from django.db import models

class Event(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('CONFIRMED', 'CONFIRMED'),
        ('REJECTED','REJECTED')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    height = models.IntegerField()
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    public_key = models.TextField()
    signature = models.TextField()
    hash = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64)
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

class Node(models.Model):
    node_id = models.CharField(max_length=100, unique=True)
    public_key = models.TextField()
    url = models.URLField()
    def __str__(self):
        return self.node_id

# These tables need to delete, only for testing purpose
class KeyPair(models.Model):    
    public_key = models.TextField(unique=True)
    private_key = models.TextField(unique=True)
    note = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f'{self.note}:{self.public_key[:5]}...'

class ErrorLog(models.Model):
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        from django.utils import timezone
        local_time = timezone.localtime(self.created_at)
        formattedtime = local_time.strftime("%Y-%m-%d %H:%M:%S")
        return f'{formattedtime} - {self.text.split('\n')[0]}'