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

## Create Identity

login to django admin and create an Identity with: 

publickey = "a5a4951a4f45b40b7c90a7e0faa4f974348c97c3aa6c63102a9363ccd48fa032"
nonce = 0

## Sign Event Data (Client Side)
```
import json

payload = {
    "image_hash":"123456",
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
  "public_key": "a5a4951a4f45b40b7c90a7e0faa4f974348c97c3aa6c63102a9363ccd48fa032",
  "signature": "be16107d66cbef1eab32c0ffea6a0e6d9cf5c11cfc40661cf3481792c1c69bf9864b25526896457b0becfb461cb78d3828ac677c9f4ccf68d47fa9ce60a26b0f",
  "timestamp": 1700000000
}'
```