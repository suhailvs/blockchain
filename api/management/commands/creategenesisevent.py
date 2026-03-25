import uuid
from django.core.management.base import BaseCommand
from api.models import Transaction
from api.utils import calculate_transaction_hash

class Command(BaseCommand):
    help = "Create Genesis Transaction."

    def handle(self, *args, **options):
        if Transaction.objects.filter(status="CONFIRMED").exists():
            self.stdout.write("Error: Genesis already exists")
            return 
        
        txn_data = {
            "tx_type": 1,
            "public_key": "SYSTEM",
            "receiver_pubkey": "",
            "amount": 0,
            "previous_hash": "0" * 64,
            "height":0,
        }
        txn_hash = calculate_transaction_hash(txn_data)
        Transaction.objects.create(
            height=txn_data["height"],
            tx_type=txn_data["tx_type"],
            public_key=txn_data['public_key'],
            receiver_pubkey=txn_data["receiver_pubkey"],
            amount=txn_data["amount"],
            signature="GENESIS",
            previous_hash=txn_data['previous_hash'],
            hash=txn_hash,
            status="CONFIRMED"
        )
        self.stdout.write(
            self.style.SUCCESS('GENESIS Transaction Created Successfully.')
        )
        print(txn_hash)