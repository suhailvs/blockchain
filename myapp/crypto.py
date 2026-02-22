import nacl.signing
import nacl.encoding
import json

def verify_signature(public_key_hex, signature_hex, payload_dict):
    try:
        verify_key = nacl.signing.VerifyKey(
            public_key_hex,
            encoder=nacl.encoding.HexEncoder
        )

        message = json.dumps(payload_dict, sort_keys=True).encode()
        verify_key.verify(message, bytes.fromhex(signature_hex))
        return True
    except Exception:
        return False