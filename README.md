# Crypto APP

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

publickey = "4a60c48ebb57b200b9938ac1c0504c2da43494aa4f938787051371e3376aeadc"
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
curl -X POST http://127.0.0.1:8000/crypto/submit/ \
  -H "Content-Type: application/json" \
  -d '{
  "event_type": "update_profile_image",
  "payload": {
    "image_hash":"123458",
    "nonce": 3
  },
  "public_key": "4a60c48ebb57b200b9938ac1c0504c2da43494aa4f938787051371e3376aeadc",
  "signature": "33ddab789fb68af7f51f2f8fe1332821f03d7209578aaaea183d333716d368083064490f28bcc2e324d889e06e99a11d80a6745585c0bc6cb1f8370fa1ecd30e",
  "timestamp": 1771758151
}'
```