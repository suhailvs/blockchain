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

def create_genesis_event():
    # ./manage.py shell < t.py
    from crypto.utils import calculate_event_hash
    from crypto.models import Event
    if Event.objects.exists(): 
        print('Event Exists')
        return None
    GENESIS_ID=1
    event_data = {
        "id": str(GENESIS_ID),
        "event_type": "GENESIS",
        "payload": {"message": "Initial event"},
        "timestamp": 0,
        "public_key": "SYSTEM",
        "previous_hash": "0" * 64,
    }

    event_hash = calculate_event_hash(event_data['id'],event_data)
    print('Event Created')
    return Event.objects.create(
        id=GENESIS_ID,
        event_type="GENESIS",
        payload=event_data["payload"],
        public_key="SYSTEM",
        signature="GENESIS",
        timestamp=0,
        previous_hash="0" * 64,
        hash=event_hash,
        status="CONFIRMED"
    )

# generate_keys()
# create_genesis_event()
# generate_signature('b9aef0880ccd51973cba5335232c8199a63055a961cb82a0f205e8013c39f146')
