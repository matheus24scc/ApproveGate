"""ApproveGate — cryptographic attestation of approvals (contextlock-inspired DSSE envelope)."""
from __future__ import annotations
import json, os, base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

KEY_PATH = Path(os.environ.get("APPROVEGATE_KEY", "keys/approvegate.key"))

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()

def load_or_create_key(path: Path = KEY_PATH) -> Ed25519PrivateKey:
    if path.exists():
        return serialization.load_pem_private_key(path.read_bytes(), password=None)
    key = Ed25519PrivateKey.generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                       serialization.NoEncryption()))
    return key

def sign(payload: dict, key: Ed25519PrivateKey | None = None) -> dict:
    """DSSE-style envelope: payload + signature proving integrity + provenance."""
    key = key or load_or_create_key()
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    sig = key.sign(body)
    return {
        "payloadType": "application/vnd.approvegate.approval+json",
        "payload": _b64(body),
        "signatures": [{"keyid": "", "sig": _b64(sig)}],
    }

def verify(envelope: dict, key: Ed25519PrivateKey | None = None) -> bool:
    key = key or load_or_create_key()
    try:
        body = base64.b64decode(envelope["payload"])
        sig = base64.b64decode(envelope["signatures"][0]["sig"])
        key.public_key().verify(sig, body)
        json.loads(body)
        return True
    except Exception:
        return False
