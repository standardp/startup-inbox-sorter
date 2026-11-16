"""AES-GCM encryption for the dashboard data, compatible with WebCrypto in docs/index.html."""
import base64
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 310_000


def _key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    return kdf.derive(passphrase.encode())


def encrypt(data: dict, passphrase: str) -> dict:
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_key(passphrase, salt)).encrypt(iv, json.dumps(data).encode(), None)
    b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iterations": ITERATIONS, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}


def decrypt(blob: dict, passphrase: str) -> dict:
    salt, iv, ct = (base64.b64decode(blob[k]) for k in ("salt", "iv", "ct"))
    key = _key(passphrase, salt) if blob.get("iterations", ITERATIONS) == ITERATIONS else PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=blob["iterations"]
    ).derive(passphrase.encode())
    return json.loads(AESGCM(key).decrypt(iv, ct, None))
