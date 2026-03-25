import json
import hashlib
import requests
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from django.db import transaction
from django.conf import settings
from django.db.models import F
from .models import Transaction, Identity,Node, ErrorLog

def get_peers():
    return Node.objects.exclude(node_id=settings.LOCAL_NODE_ID)

def apply_transaction(tx):
    print('-'*40)
    print('APPLY TRANSACTION')
    print('-'*40)
    if tx.tx_type == 1:#"register"
        identity = Identity.objects.create(public_key=tx.public_key)
        print('New user created:',identity)

    elif tx.tx_type == 2: # "transfer"
        sender = Identity.objects.get(public_key=tx.public_key)        
        sender.balance = F('balance') - tx.amount        
        # sender.nonce = max(sender.nonce, nonce)
        sender.save()

        receiver = Identity.objects.get(public_key=tx.receiver_pubkey)
        receiver.balance = F('balance') + tx.amount
        receiver.save()

def confirm_transaction(txn):
    if Transaction.objects.filter(height=txn.height, status="CONFIRMED").exists():
        # reject_this_transaction
        txn.status = "REJECTED"
    else:
        txn.status = "CONFIRMED"
    txn.save()
    apply_transaction(txn)

def calculate_transaction_hash(txn):
    data = json.dumps({
        "tx_type": txn["tx_type"],
        "public_key": txn['public_key'],
        "receiver_pubkey": txn.get('receiver_pubkey'),
        "amount": txn['amount'],
        "height": txn['height'],
        "previous_hash": txn['previous_hash'],
    }, sort_keys=True)
    
    return hashlib.sha256(data.encode()).hexdigest()

def generate_signature(message):
    private_key = SigningKey(settings.NODE_PRIVATE_KEY, encoder=HexEncoder)
    signed = private_key.sign(message.encode())
    return signed.signature.hex()

def verify_signature(public_key_hex, signature_hex, payload):
    try:
        public_key = VerifyKey(public_key_hex,encoder=HexEncoder)
        if isinstance(payload, str):
            message = payload
        else:
            message = json.dumps(payload, sort_keys=True)
        public_key.verify(message.encode(), bytes.fromhex(signature_hex))
        return True
    except Exception as e:
        print('='*50)
        print(e)
        print('-'*50)
        print('public_key_hex:',public_key_hex)
        print('signature_hex:',signature_hex)
        print('Payload:',payload)
        print('='*50)
        return False

def count_valid_finalize_signatures(txn_hash, signature_list):
    valid_signatures = 0
    in_valid_signatures = 0
    seen_keys = set()

    for item in signature_list:
        public_key = item.get("public_key")
        vote_signature = item.get("signature")

        if not public_key or not vote_signature:
            continue

        if public_key in seen_keys:
            continue

        if not Node.objects.filter(public_key=public_key).exists():
            continue

        if verify_signature(public_key, vote_signature, f"FINALIZE:{txn_hash}"):
            valid_signatures += 1
            seen_keys.add(public_key)
        else:
            in_valid_signatures += 1
    print('VALID SIGNATURES:',valid_signatures,', INVALID SIGNATURES:',in_valid_signatures)
    return valid_signatures
    

def verify_and_add_transaction(txn_data, is_sync_blockchain=False):
    with transaction.atomic():
        tx_type = txn_data["tx_type"]
        public_key = txn_data["public_key"]
        signature = txn_data["signature"]
        previous_hash = txn_data["previous_hash"]
        receiver_pubkey = txn_data.get("receiver_pubkey")
        amount = txn_data["amount"]
        height = txn_data["height"]        

        if tx_type not in dict(Transaction.TX_TYPE_CHOICES):
            raise Exception("Invalid tx_type")
        if tx_type == 1:
            if Identity.objects.filter(public_key=public_key):
                raise Exception("User Already exists.")
        # Verify signature
        signed_payload = {
            "tx_type": tx_type,
            "public_key": public_key,
            "receiver_pubkey": receiver_pubkey,
            "amount": amount,
            "height": height,
            "previous_hash": previous_hash,
        }
        if not verify_signature(public_key, signature, signed_payload):
            raise Exception("Invalid signature")
        last_txn = Transaction.objects.filter(
            status="CONFIRMED"
        ).order_by("-height").first()

        if txn_data["previous_hash"] != last_txn.hash:
            raise Exception("Previous Hash doesn't match")

        if height != last_txn.height + 1:
            raise Exception("Replay attack detected or invalid height.")
        
        txn_hash = calculate_transaction_hash(txn_data)

        if Transaction.objects.filter(hash=txn_hash).exists():
            raise Exception("Duplicate transaction")

        if is_sync_blockchain:
            expected_hash = txn_hash
            if txn_data["hash"] != expected_hash:
                raise Exception("Invalid transaction hash during sync")
            new_status = "CONFIRMED"
            votes = []
        else:
            new_status = "PENDING"
            votes = [{
                "public_key": Node.objects.get(node_id=settings.LOCAL_NODE_ID).public_key,
                "signature": generate_signature(f"FINALIZE:{txn_hash}"),
            }]

        # Store immutable transaction
        txn = Transaction.objects.create(
            hash=txn_hash,
            height=height,
            tx_type=tx_type,
            public_key=public_key,
            receiver_pubkey=receiver_pubkey,
            amount=amount,
            signature=signature,
            previous_hash=previous_hash,
            votes=votes,
            status=new_status,
        )

        if is_sync_blockchain:
            apply_transaction(txn)
        
        return txn

def sync_transactions():
    txns_synced = 0
    for peer in get_peers():
        while True:
            # api/transactions/ only will give 100 transactions per request so need to run loop
            last_txn = Transaction.objects.filter(
                status="CONFIRMED"
            ).order_by("-height").first()
            try:
                response = requests.get(
                    f"{peer.url}/api/transactions/",
                    params={"after_hash": last_txn.hash},
                    timeout=5
                )
                if response.status_code != 200:
                    ErrorLog.objects.create(text=f"Error while syncing peer {peer.url}\n\nStatus Code: {response.status_code}")
                    break
                remote_txns = response.json().get("transactions", [])
                if not remote_txns:
                    # sync completed
                    break
                for txn_data in remote_txns:
                    if not verify_and_add_transaction(
                        txn_data,
                        is_sync_blockchain=True,
                    ):
                        break  # stop if chain breaks
                    else:txns_synced+=1
            except Exception as e:
                ErrorLog.objects.create(text=f'Error syncing from peer {peer.url}/api/transactions/\n\n{e}')
                break
    return txns_synced
