import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_KEY = None

def _get_key() -> bytes:
    global _KEY
    if _KEY is not None:
        return _KEY
    load_dotenv()
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if len(raw) < 64:
        raise ValueError("ENCRYPTION_KEY must be at least 64 hex characters")
    _KEY = bytes.fromhex(raw[:64])
    return _KEY

def encrypt(data: bytes) -> bytes:
    key = _get_key()
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, data, None)

def decrypt(data: bytes) -> bytes:
    return AESGCM(_get_key()).decrypt(data[:12], data[12:], None)
