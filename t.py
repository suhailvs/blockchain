# https://pynacl.readthedocs.io/en/latest/signing/#id1
# Ed25519
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from mnemonic import Mnemonic
import json

def ed25519_key_from_mnemonic(mnemonic_phrase):
    # Example usage
    # ed25519_key_from_mnemonic('bachelor clap draw nerve feature capital entire silly tower letter negative interest slogan bring sword abstract drift noodle middle discover armed undo pact donate')
    mnemo = Mnemonic("english") 
    if not mnemo.check(mnemonic_phrase):
        raise ValueError("Invalid mnemonic phrase")
    seed = mnemo.to_seed(mnemonic_phrase, passphrase = "")
    # Use first 32 bytes for Ed25519 private key
    private_key = SigningKey(seed[:32])
    public_key = private_key.verify_key
    private_key_hex = private_key.encode(encoder=HexEncoder).decode()
    public_key_hex = public_key.encode(encoder=HexEncoder).decode()       
    print("Mnemonic 24 words:", mnemonic_phrase)
    print("Public Key:", public_key_hex)
    print("Private Key:", private_key_hex)

def generate_signature(private_key_hex):    
    private_key = SigningKey(private_key_hex,encoder=HexEncoder)
    signing_payload = {
        "tx_type": 2,
        "public_key": "b75ec7154c3f830b093e87c7b8145db809c63e5890b3964e83bdb5a26b5db58d",
        "receiver_pubkey": "9692355f209282a3d5e34bd34207df8db87c5d96f4f58a44883bbd0d9d9222fa",
        "amount": 10,
        "height": 1,
        "previous_hash": "471859163112f969898719911505099ff8a1aa3e9563d584f2c552384895a2f7",
    }
    message = json.dumps(signing_payload, sort_keys=True)
    signed = private_key.sign(message.encode())
    print("Signature:", signed.signature.hex())

# ed25519_key_from_mnemonic(Mnemonic("english").generate(strength=256)) # 24 words
generate_signature(private_key_hex='b9aef0880ccd51973cba5335232c8199a63055a961cb82a0f205e8013c39f146')


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
    signing_payload = {
        "tx_type": 2,
        "public_key": "SENDER_PUBLIC_KEY",
        "receiver_pubkey": "RECEIVER_PUBLIC_KEY",
        "amount": 1,
        "timestamp": 1,
        "previous_hash": "9f901266d041aa9689439440be314fd1d4d7eb597ddad339480bf193f437c607",
    }
    message = json.dumps(signing_payload, sort_keys=True)
    public_key.verify(message.encode(), bytes.fromhex(signature))
