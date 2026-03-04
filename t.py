# https://pynacl.readthedocs.io/en/latest/signing/#id1
# Ed25519
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
import json

def generate_keys():
    private_key = SigningKey.generate()
    public_key = private_key.verify_key
    private_key_hex = private_key.encode(encoder=HexEncoder).decode()
    public_key_hex = public_key.encode(encoder=HexEncoder).decode()
    print("Public Key:", public_key_hex)
    print("Private Key:", private_key_hex)

def generate_signature(private_key_hex):    
    private_key = SigningKey(private_key_hex,encoder=HexEncoder)
    payload = {
        "image_hash":"123458",
        "nonce": 1
    }
    message = json.dumps(payload, sort_keys=True)
    # message = 'hai'
    signed = private_key.sign(message.encode())
    print("Signature:", signed.signature.hex())

def create_genesis_event_using_utils():
    # ./manage.py shell < t.py
    from api.models import Event
    from api.utils import calculate_event_hash
    
    if Event.objects.filter(status="CONFIRMED").exists(): 
        print('Event Exists')
        return None
    GENESIS_ID=1
    height = 0
    event_data = {
        "event_type": "GENESIS",
        "payload": {"message": "Initial event"},
        "public_key": "SYSTEM",
        "previous_hash": "0" * 64,
    }

    event_hash = calculate_event_hash(str(GENESIS_ID),event_data,height)
    print('Event Created')
    return Event.objects.create(
        id=GENESIS_ID,
        height=height,
        event_type=event_data['event_type'],
        payload=event_data["payload"],
        public_key=event_data['public_key'],
        signature="GENESIS",
        previous_hash=event_data['previous_hash'],
        hash=event_hash,
        status="CONFIRMED"
    )

# generate_keys()
# generate_signature(private_key_hex='b9aef0880ccd51973cba5335232c8199a63055a961cb82a0f205e8013c39f146')
create_genesis_event_using_utils()


# not used
def docs():
    signing_key = SigningKey.generate()
    signed_hex = signing_key.sign(b"Attack at Dawn", encoder=HexEncoder)
    public_key = signing_key.verify_key
    public_key_hex = public_key.encode(encoder=HexEncoder)
    public_key = VerifyKey(public_key_hex, encoder=HexEncoder)
    # Check the validity of a message's signature
    public_key.verify(signed_hex, encoder=HexEncoder)
    # The message and the signature can either be passed together, or separately
    signature_bytes = HexEncoder.decode(signed_hex.signature)
    public_key.verify(signed_hex.message, signature_bytes,
                    encoder=HexEncoder)

def verify_signature(public_key_hex,signature):
    public_key = VerifyKey(public_key_hex, encoder=HexEncoder)
    payload = {
        "image_hash":"123458",
        "nonce": 1
    }
    message = json.dumps(payload, sort_keys=True)
    # message = 'hai'
    public_key.verify(message.encode(), bytes.fromhex(signature))
