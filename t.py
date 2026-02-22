import nacl.signing
# Generate private key
private_key = nacl.signing.SigningKey.generate()

def a():
    import nacl.encoding
    # Get public key
    public_key = private_key.verify_key

    # Convert to hex (store/send safely)
    private_key_hex = private_key.encode(encoder=nacl.encoding.HexEncoder).decode()
    public_key_hex = public_key.encode(encoder=nacl.encoding.HexEncoder).decode()

    print("Private Key:", private_key_hex)
    print("Public Key:", public_key_hex)

def b():
    import json
    payload = {
        "image_hash":"123456",
        "nonce": 1
    }
    message = json.dumps(payload, sort_keys=True).encode()
    signature = private_key.sign(message)
    signature_hex = signature.signature.hex()
    print("Signature:", signature_hex)

a()
b()