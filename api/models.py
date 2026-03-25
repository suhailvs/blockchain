import uuid
from django.db import models

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('CONFIRMED', 'CONFIRMED'),
        ('REJECTED','REJECTED')]
    
    TX_TYPE_CHOICES = [
        (1, 'REGISTER_USER'),
        (2, 'TRANSFER'),
        # (3, 'ADJUST_CREDIT_LIMIT'),
        # (4, 'TRUST_LINK'), # social graph
        # (5, 'NODE_REGISTER'), # P2P node
    ]
    hash = models.CharField(primary_key=True, max_length=64, unique=True)
    tx_type = models.SmallIntegerField(default=2,choices=TX_TYPE_CHOICES)
    height = models.IntegerField()
    public_key = models.CharField(max_length=64, db_index=True) # sender pubkey    
    receiver_pubkey = models.CharField(max_length=64, db_index=True,null=True)
    amount = models.PositiveIntegerField(default=0)    
    signature = models.CharField(max_length=128)    
    previous_hash = models.CharField(max_length=64)
    votes = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, default="PENDING",choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["height"],
                condition=models.Q(status="CONFIRMED"),
                name="unique_confirmed_height"
            )]
    def __str__(self):
        return f'{self.status}:{self.hash[:5]}... {self.public_key[:6]} -> {self.receiver_pubkey[:6] if self.receiver_pubkey else '-'} ({self.amount})'

class Identity(models.Model):
    public_key = models.CharField(max_length=64, unique=True, db_index=True)
    balance = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    # nonce = models.BigIntegerField(default=0)  # Prevent replay attacks
    
    @property
    def balance_from_txns(self):
        received = Transaction.objects.filter(receiver_pubkey=self.public_key).aggregate(t=models.Sum('amount'))['t'] or 0
        send = Transaction.objects.filter(public_key=self.public_key).aggregate(t=models.Sum('amount'))['t'] or 0
        return received - send

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
        formattedtime = local_time.strftime("%d %b %Y %I:%M %p")
        return f'{formattedtime} - {self.text.split('\n')[0]}'
