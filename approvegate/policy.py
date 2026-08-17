"""ApproveGate — risk scoring + approval policy for agent actions."""
from __future__ import annotations

RISK_WEIGHTS = {
    "delete": 40, "drop": 50, "push": 20, "exec": 30, "payment": 45,
    "send_message": 10, "create": 5, "update": 10, "read": 0, "query": 0,
}

def risk_score(action: dict) -> int:
    op = str(action.get("op", "")).lower()
    score = RISK_WEIGHTS.get(op, 15)
    if action.get("uses_credentials"):
        score += 20
    if action.get("external_network"):
        score += 10
    if action.get("target_sensitivity") == "high":
        score += 15
    return min(score, 100)

def requires_approval(action: dict, score: int) -> bool:
    if action.get("deny"):
        return True
    return score >= 50
