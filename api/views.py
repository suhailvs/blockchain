import requests
import uuid
import time

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.decorators import throttle_classes
from rest_framework.views import APIView
from django.conf import settings
from .utils import (verify_and_add_transaction, count_valid_finalize_signatures,
    generate_signature,confirm_transaction,get_peers, sync_transactions)
from .models import Transaction,Node, ErrorLog
from .auth import consensus_required, create_consensus_auth_headers
ErrorResponse = lambda error: Response({"error":error},status=404)

def serialize_txn(txn):
    return {
        "hash": txn.hash,
        "tx_type": txn.tx_type,
        "height":txn.height,        
        "public_key": txn.public_key,
        "receiver_pubkey": txn.receiver_pubkey,
        "amount": txn.amount,
        "signature": txn.signature,
        "previous_hash": txn.previous_hash,            
    }

class GetTransactionsAfterThrottle(AnonRateThrottle):
    rate = "10/min"
class SubmitTransactionThrottle(AnonRateThrottle):
    rate = "60/min"

@api_view(["GET"])
def home(request):
    last_txn = Transaction.objects.filter(
        status="CONFIRMED"
    ).order_by("-height").first()
    return Response({"height": last_txn.height,"hash":last_txn.hash})


@api_view(["GET"])
@throttle_classes([GetTransactionsAfterThrottle])
def get_transactions_after(request):
    LIMIT = 100
    after_hash = request.GET.get("after_hash")
    if not after_hash:
        return ErrorResponse("after_hash required")
    try:
        last_txn = Transaction.objects.get(hash=after_hash)
    except Transaction.DoesNotExist:
        return ErrorResponse("hash not found")
    txns = Transaction.objects.filter(
        height__gt=last_txn.height,
        status="CONFIRMED"
    ).order_by("height")
    data = [serialize_txn(txn) for txn in txns[:LIMIT]]
    return Response({"transactions": data})


class TransactionSubmissionView(APIView):
    throttle_classes = [SubmitTransactionThrottle]

    def get_network_latest(self,local_height):
        heights = []
        for peer in get_peers():
            try:
                r = requests.get(f"{peer.url}/", timeout=5)
                data = r.json()
                heights.append(data["height"])
            except Exception as e:
                ErrorLog.objects.create(text=f'Get peers error for peer {peer.url}/\n\n{e}')
                continue
        heights.append(local_height)
        return heights
    
    def broadcast_transaction(self, txn, total_nodes):
        txn_data = serialize_txn(txn)
        
        approvals = 0
        for peer in get_peers():
            try:
                HEADERS = create_consensus_auth_headers(
                    method="POST",
                    path="/api/validate/",
                    body=txn_data
                )
                response = requests.post(
                    f"{peer.url}/api/validate/",
                    json=txn_data,
                    headers=HEADERS,
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("approved") and data.get("signature"):
                        # Keep one vote per validator public key.
                        votes = [v for v in txn.votes if v.get("public_key") != peer.public_key]
                        votes.append({"public_key": peer.public_key,"signature": data["signature"]})
                        txn.votes = votes
                        txn.save(update_fields=["votes"])
                    # check_majority
                    if txn.status != "CONFIRMED":
                        approvals = count_valid_finalize_signatures(txn.hash, txn.votes)
                        if approvals > total_nodes / 2:
                            confirm_transaction(txn)
            except Exception as e:
                ErrorLog.objects.create(text=f'Broadcast error at peer {peer.url}/api/validate/\n\n{e}')
                print('Broadcast error:',peer.url,e)
                continue
        return approvals

    def broadcast_finalization(self, txn):
        data = {
            "transaction_hash": txn.hash,
            "signature_list": txn.votes,
        }
        for peer in get_peers():
            try:
                HEADERS = create_consensus_auth_headers(
                    method="POST",
                    path="/api/finalize-transaction/",
                    body=data
                )
                response = requests.post(
                    f"{peer.url}/api/finalize-transaction/",
                    json=data,
                    headers=HEADERS,
                    timeout=3
                )
                print(peer.url,response.json())
            except Exception as e:
                ErrorLog.objects.create(text=f'Broadcast finalization error at peer {peer.url}/api/finalize-transaction/\n\n{e}')
                print('Broadcast finalization error:',peer.url,e)
                continue

    def post(self, request, format=None):
        local = Transaction.objects.filter(status="CONFIRMED").order_by("-height").first()
        heights = self.get_network_latest(local.height)
        if max(heights) > local.height:
            # "Node behind. Syncing first."
            sync_transactions()
        
        try:
            txn = verify_and_add_transaction(request.data)
        except Exception as e:
            return ErrorResponse(str(e))
        total_nodes = Node.objects.count()
        approvals = self.broadcast_transaction(txn, total_nodes)
        if approvals > total_nodes / 2:
            self.broadcast_finalization(txn)
        return Response({"transaction_hash": txn.hash})
      


@api_view(["POST"])
@consensus_required
def validate_transaction(request):
    try:
        txn = verify_and_add_transaction(request.data)
        local_signature = generate_signature(f"FINALIZE:{txn.hash}")
        
        return Response({"approved": True,"signature": local_signature})    
    except Exception as e:
        return ErrorResponse(str(e))

@api_view(["POST"])
@consensus_required
def finalize_transaction(request):
    txn_hash = request.data["transaction_hash"]
    signature_list = request.data["signature_list"]
    try:
        txn = Transaction.objects.get(hash=txn_hash)
    except Transaction.DoesNotExist:
        # since we call finalize before all peers transactions update, we get error Transaction matching query does not exist.
        # TODO: don't know wheter to return 404 or do a sync_transactions function
        # return Response({"error": "Transaction not found"}, status=404)
        # print('Transaction not found. So sync transactions')
        # sync_transactions()
        # return Response({"status": Transaction.objects.get(id=txn_id).status})
        return ErrorResponse("Transaction not found")
        
    if txn.hash != txn_hash:
        return ErrorResponse("Hash mismatch")
    valid_signatures = count_valid_finalize_signatures(txn_hash, signature_list)

    if valid_signatures > Node.objects.count() / 2:
        txn.votes = signature_list
        txn.save(update_fields=["votes"])
        if txn.status != "CONFIRMED":
            confirm_transaction(txn)
        return Response({"status": "CONFIRMED"})

    return Response({"status": "PENDING", "valid_signatures": valid_signatures}, status=202)
