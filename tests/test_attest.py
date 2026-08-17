"""Testes de atestado criptográfico (contextlock-inspired DSSE envelope)."""
import base64, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from approvegate.attest import sign, verify, load_or_create_key
from approvegate.gateway import Gateway
from approvegate.approver import MockApprover

def test_sign_verify_roundtrip():
    payload = {"id": 1, "op": "delete", "decision": "approved"}
    env = sign(payload)
    assert verify(env) is True

def test_tamper_payload_detected():
    env = sign({"id": 1, "op": "delete", "decision": "approved"})
    body = json.loads(base64.b64decode(env["payload"]))
    body["decision"] = "rejected"
    env["payload"] = base64.b64encode(json.dumps(body).encode()).decode()
    assert verify(env) is False

def test_wrong_key_rejected():
    env = sign({"id": 1})
    other = Ed25519PrivateKey.generate()
    assert verify(env, key=other) is False

def test_gateway_signed_verify_all():
    gw = Gateway(MockApprover("approved"))
    gw.request({"op": "read"})
    gw.request({"op": "delete", "target_sensitivity": "high", "uses_credentials": True})
    assert gw.signed_verify_all() is True
    gw.signed[0]["signatures"][0]["sig"] = base64.b64encode(b"x" * 64).decode()
    assert gw.signed_verify_all() is False
