# https://chatgpt.com/s/t_69a96791a03c819182c06ac7e1c4c6f7

from functools import wraps
import time
import json
import hashlib
from rest_framework.response import Response
from django.conf import settings
from .models import Node
from .utils import verify_signature, generate_signature

def consensus_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        node_id = request.headers.get("X-Node-Id")
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")
        node = Node.objects.filter(node_id=node_id).first()
        if not node:
            return Response({"error": "Unauthorized: Given node_id not in TRUSTED_PEERS"}, status=401)
        
        if abs(time.time() - int(timestamp)) > 5: # replay protection (5 seconds window)
            return Response({"error": "Unauthorized: Replay attack detected"}, status=401)

        body_dict = json.loads(request.body.decode())
        canonical_body = json.dumps(body_dict, separators=(",", ":"), sort_keys=True)
        body_hash = hashlib.sha256(canonical_body.encode()).hexdigest()
        message = f"{request.method}|{request.path}|{body_hash}|{timestamp}"

        if not verify_signature(node.public_key,signature,message):
            return Response({"error": "Unauthorized: Signature not match."}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view

def create_consensus_auth_headers(method, path, body):
    timestamp = str(int(time.time()))
    canonical_body = json.dumps(body, separators=(",", ":"), sort_keys=True)
    body_hash = hashlib.sha256(canonical_body.encode()).hexdigest()
    message = f"{method.upper()}|{path}|{body_hash}|{timestamp}"
    return {
        "X-Node-Id": settings.LOCAL_NODE_ID,
        "X-Signature": generate_signature(message),
        "X-Timestamp": timestamp,
        "Content-Type": "application/json",
    }