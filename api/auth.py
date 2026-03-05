# https://chatgpt.com/s/t_69a96791a03c819182c06ac7e1c4c6f7

from functools import wraps
import time
import json
from rest_framework.response import Response
from .models import Node
from .utils import verify_signature, generate_signature

def consensus_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        public_key = request.headers.get("X-Public-Key")
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")

        if not Node.objects.filter(public_key=public_key):
            return Response({"error": "Unauthorized: Given public key not in TRUSTED_PEERS"}, status=401)
        
        if abs(time.time() - int(timestamp)) > 5: # replay protection (5 seconds window)
            return Response({"error": "Unauthorized: Replay attack detected"}, status=401)

        body = request.body.decode()
        message = f"{request.method}|{request.path}|{body}|{timestamp}"

        if not verify_signature(public_key,signature,message):
            return Response({"error": "Unauthorized: Signature not match."}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view

def create_consensus_auth_headers(method, path, body):
    timestamp = str(int(time.time()))
    body_json = json.dumps(body or {}, separators=(",", ":"), sort_keys=True)
    message = f"{method.upper()}|{path}|{body_json}|{timestamp}"
    return {
        "X-Public-Key": NODE_PUBLIC_KEY,
        "X-Signature": generate_signature(message),
        "X-Timestamp": timestamp,
        "Content-Type": "application/json",
    }