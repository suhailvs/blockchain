import nacl.signing


def generate_keys():
    import nacl.encoding
    private_key = nacl.signing.SigningKey.generate()
    public_key = private_key.verify_key

    # Convert to hex (store/send safely)
    private_key_hex = private_key.encode(encoder=nacl.encoding.HexEncoder).decode()
    public_key_hex = public_key.encode(encoder=nacl.encoding.HexEncoder).decode()
    print("Public Key:", public_key_hex)
    print("Private Key:", private_key_hex)
    

def generate_signature(private_key_hex):
    import json
    private_key = nacl.signing.SigningKey(
        private_key_hex,
        encoder=nacl.encoding.HexEncoder
    )
    payload = {
        "image_hash":"123458",
        "nonce": 1
    }
    message = json.dumps(payload, sort_keys=True).encode()
    signature = private_key.sign(message)
    signature_hex = signature.signature.hex()
    print("Signature:", signature_hex)

def create_genesis_event_using_utils():
    # ./manage.py shell < t.py
    from crypto.utils import create_genesis_event
    create_genesis_event()

# generate_keys()
# create_genesis_event_using_utils()
generate_signature('b9aef0880ccd51973cba5335232c8199a63055a961cb82a0f205e8013c39f146')
