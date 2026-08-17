"""Testes de politica em YAML + deny-list."""
from pathlib import Path
from approvegate.policy import Policy, load_policy, risk_score, requires_approval


def test_yaml_load(tmp_path):
    p = tmp_path / "policy.yaml"
    p.write_text("threshold: 30\nweights:\n  read: 10\ndeny_list:\n  - op: drop\n  - tool: rm\n",
                 encoding="utf-8")
    pol = load_policy(p)
    assert pol.threshold == 30
    assert pol.risk_score({"op": "read"}) == 10
    assert pol.requires_approval({"op": "drop"}, 5) is True
    assert pol.requires_approval({"op": "x", "tool": "rm"}, 5) is True
    assert pol.requires_approval({"op": "read"}, 10) is False


def test_default_unchanged():
    assert risk_score({"op": "read"}) == 0
    assert requires_approval({"op": "delete", "target_sensitivity": "high", "uses_credentials": True}, 90)


def test_gateway_uses_policy(tmp_path):
    from approvegate.gateway import Gateway
    from approvegate.approver import MockApprover
    p = tmp_path / "policy.yaml"
    p.write_text("threshold: 30\n", encoding="utf-8")
    gw = Gateway(MockApprover("approved"), policy=load_policy(p))
    # read normally auto-allows; with threshold 30 it now requires approval
    r = gw.request({"op": "read", "uses_credentials": True})  # score 20 < 30 -> allowed
    assert r["status"] == "executed"
    r2 = gw.request({"op": "read", "uses_credentials": True, "external_network": True})  # 20+10=30 >=30
    assert r2["status"] == "executed"  # MockApprover approves
