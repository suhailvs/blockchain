# pip install pynacl, stellar_sdk
# this is just a demonstration of how stellar create keys, signature and verify
import base64
import hashlib

def crc16_xmodem(data: bytes):
    crc = 0x0000
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc.to_bytes(2, "little")

def nacl_test():
    from nacl.signing import SigningKey
    print('\n','#'*50,'\n',"Using PyNaCl library",'\n','#'*50)
    signing_key = SigningKey.generate()
    # -----------------------
    # Stellar Publickey
    # -----------------------
    verify_key = signing_key.verify_key
    raw_public_key = verify_key.encode()  # 32 bytes
    version_byte = b'\x30'  # 6 << 3 for public key
    payload = version_byte + raw_public_key
    checksum = crc16_xmodem(payload)
    stellar_address = base64.b32encode(payload + checksum).decode().replace("=", "")
    print("Stellar Address:", stellar_address)

    # -----------------------
    # Stellar Secret key
    # -----------------------
    raw_seed = signing_key.encode()  # 32 bytes
    version_byte = b'\x90'  # 18 << 3 for secret seed
    payload = version_byte + raw_seed
    checksum = crc16_xmodem(payload)
    stellar_secret = base64.b32encode(payload + checksum).decode().replace("=", "")
    print("Stellar Secret:", stellar_secret)

    # -----------------------
    # Stellar Signature
    # -----------------------
    message = b"hello stellar"
    hashed = hashlib.sha256(message).digest()
    signature = signing_key.sign(hashed).signature
    print("Signature (hex):", signature.hex())

    # -----------------------
    # Stellar Verify
    # -----------------------
    verify_key.verify(hashed, signature)
    print("Signature is valid")
    return stellar_secret

def stellar_test(stellar_secret):
    from stellar_sdk import Keypair
    print('\n','#'*50,'\n',"Using Stellar-SDK library",'\n','#'*50)
    keypair = Keypair.from_secret(stellar_secret)
    print("Stellar Address:", keypair.public_key)


    message = b"hello stellar"
    hashed = hashlib.sha256(message).digest()
    signature = keypair.sign(hashed)
    print("Signature (hex):", signature.hex())

    public_key = keypair.public_key
    kp = Keypair.from_public_key(public_key)
    kp.verify(hashed, signature)
    print("Signature is valid")

secret = nacl_test()
stellar_test(secret)