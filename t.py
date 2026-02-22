import nacl.signing


def a():
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

def b(private_key_hex):
    import json
    private_key = nacl.signing.SigningKey(
        private_key_hex,
        encoder=nacl.encoding.HexEncoder
    )
    payload = {
        "image_hash":"123458",
        "nonce": 3
    }
    message = json.dumps(payload, sort_keys=True).encode()
    signature = private_key.sign(message)
    signature_hex = signature.signature.hex()
    print("Signature:", signature_hex)

# a()
b('7e0e3e2f77b1a25a150cff380a381c57d5e356e72d0ede6624706d9d59e5f5d6')