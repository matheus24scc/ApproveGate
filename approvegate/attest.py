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

# ---------------------------------------------------------------------------
# Optional: Sigstore / cosign attestation (keyless, third-party verifiable)
# Requires the `cosign` CLI + an OIDC identity. Falls back gracefully when
# cosign is not installed (the local DSSE/Ed25519 path above remains default).
# ---------------------------------------------------------------------------
import shutil as _shutil
import subprocess as _subprocess
import tempfile as _tempfile

def cosign_available() -> bool:
    return _shutil.which("cosign") is not None

def sign_sigstore(payload: dict) -> dict | None:
    """Sign a payload keyless via Sigstore (`cosign sign-blob`). Returns a DSSE-style
    envelope with the cosign signature + Fulcio cert, or None if cosign is absent."""
    if not cosign_available():
        return None
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    with _tempfile.TemporaryDirectory() as td:
        blob = Path(td) / "audit.json"
        blob.write_bytes(body)
        sig = Path(td) / "audit.sig"
        cert = Path(td) / "cert.pem"
        r = _subprocess.run(["cosign", "sign-blob", "--output-signature", str(sig),
                             "--output-certificate", str(cert), str(blob)],
                            capture_output=True, text=True)
        if r.returncode != 0 or not sig.exists():
            return None
        return {
            "payloadType": "application/vnd.approvegate.audit+json",
            "payload": _b64(body),
            "signatures": [{"keyid": "", "sig": _b64(sig.read_bytes()),
                            "cert": _b64(cert.read_bytes())}],
            "backend": "sigstore/cosign",
        }

def verify_sigstore(envelope: dict) -> bool:
    if not cosign_available() or envelope.get("backend") != "sigstore/cosign":
        return False
    try:
        body = base64.b64decode(envelope["payload"])
        sig = base64.b64decode(envelope["signatures"][0]["sig"])
        cert = base64.b64decode(envelope["signatures"][0]["cert"])
    except Exception:
        return False
    with _tempfile.TemporaryDirectory() as td:
        blob = Path(td) / "audit.json"
        blob.write_bytes(body)
        sigp = Path(td) / "audit.sig"
        sigp.write_bytes(sig)
        certp = Path(td) / "cert.pem"
        certp.write_bytes(cert)
        r = _subprocess.run(["cosign", "verify-blob", "--signature", str(sigp),
                             "--certificate", str(certp), str(blob)],
                            capture_output=True, text=True)
        return r.returncode == 0
