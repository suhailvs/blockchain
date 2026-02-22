## Generate Key Pair
```
import nacl.signing
import nacl.encoding

# Generate private key
private_key = nacl.signing.SigningKey.generate()

# Get public key
public_key = private_key.verify_key

# Convert to hex (store/send safely)
private_key_hex = private_key.encode(encoder=nacl.encoding.HexEncoder).decode()
public_key_hex = public_key.encode(encoder=nacl.encoding.HexEncoder).decode()

print("Private Key:", private_key_hex)
print("Public Key:", public_key_hex)
```

## Sign Event Data (Client Side)
```
import json

payload = {
    "listing_id": "abc123",
    "price": 100,
    "nonce": 1
}

message = json.dumps(payload, sort_keys=True).encode()

signature = private_key.sign(message)

signature_hex = signature.signature.hex()

print("Signature:", signature_hex)
```

## Send to server

```
curl -X POST http://127.0.0.1:8000/submit/ \
  -H "Content-Type: application/json" \
  -d '{
  "event_type": "update_profile_image",
  "payload": {
    "image_hash":"123456",
    "nonce": 1
  },
  "public_key": "...",
  "signature": "...",
  "timestamp": 1700000000
}'
```