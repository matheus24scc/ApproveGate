"""Testes do ApproveGate (oracle test-first)."""
from approvegate.gateway import Gateway
from approvegate.approver import MockApprover
from approvegate.policy import risk_score, requires_approval

def test_low_risk_auto_allowed():
    gw = Gateway(MockApprover("approved"))
    r = gw.request({"op": "read", "target": "x.txt"})
    assert r["status"] == "executed" and r["result"].startswith("executed:")

def test_high_risk_approved_executes():
    gw = Gateway(MockApprover("approved"))
    r = gw.request({"op": "delete", "target": "db", "target_sensitivity": "high", "uses_credentials": True})
    assert r["status"] == "executed"

def test_high_risk_rejected_blocked():
    gw = Gateway(MockApprover("rejected"))
    r = gw.request({"op": "drop", "target": "table", "uses_credentials": True})
    assert r["status"] == "blocked"

def test_pending_then_approve_executes():
    gw = Gateway(MockApprover("pending"))
    r = gw.request({"op": "exec", "target": "script.sh", "uses_credentials": True, "external_network": True})
    assert r["status"] == "pending"
    r2 = gw.approve(r["id"])
    assert r2["status"] == "executed"

def test_risk_scoring():
    assert risk_score({"op": "read"}) == 0
    assert risk_score({"op": "delete", "target_sensitivity": "high", "uses_credentials": True}) >= 50
    assert requires_approval({"op": "delete", "target_sensitivity": "high", "uses_credentials": True}, 90)

def test_audit_tamper_evident():
    gw = Gateway(MockApprover("approved"))
    gw.request({"op": "read"})
    gw.request({"op": "delete", "target_sensitivity": "high", "uses_credentials": True})
    assert gw.audit.verify() is True
    gw.audit.entries[0]["data"]["op"] = "HACKED"   # adulteracao
    assert gw.audit.verify() is False
