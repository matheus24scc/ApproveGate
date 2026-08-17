"""ApproveGate — risk scoring + approval policy (supports YAML config)."""
from __future__ import annotations
from pathlib import Path
import os

try:
    import yaml
except Exception:  # pragma: no cover - yaml is an optional-but-expected dep
    yaml = None

DEFAULT_WEIGHTS = {
    "delete": 40, "drop": 50, "push": 20, "exec": 30, "payment": 45,
    "send_message": 10, "create": 5, "update": 10, "read": 0, "query": 0,
}

DEFAULT_THRESHOLD = 50


class Policy:
    """Risk policy: op weights, approval threshold, and per-tool/op deny-list."""

    def __init__(self, weights=None, threshold=DEFAULT_THRESHOLD, deny_list=None):
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self.threshold = threshold
        self.deny_list = deny_list or []  # list of {"op": ...} and/or {"tool": ...}

    @classmethod
    def from_dict(cls, data: dict) -> "Policy":
        data = data or {}
        return cls(weights=data.get("weights"), threshold=data.get("threshold", DEFAULT_THRESHOLD),
                   deny_list=data.get("deny_list"))

    def risk_score(self, action: dict) -> int:
        op = str(action.get("op", "")).lower()
        score = self.weights.get(op, 15)
        if action.get("uses_credentials"):
            score += 20
        if action.get("external_network"):
            score += 10
        if action.get("target_sensitivity") == "high":
            score += 15
        return min(score, 100)

    def requires_approval(self, action: dict, score: int) -> bool:
        if action.get("deny"):
            return True
        for d in self.deny_list:
            if ("op" in d and d["op"] == action.get("op")) or                ("tool" in d and d.get("tool") == action.get("tool")):
                return True
        return score >= self.threshold


DEFAULT_POLICY = Policy()


def risk_score(action: dict) -> int:
    return DEFAULT_POLICY.risk_score(action)


def requires_approval(action: dict, score: int) -> bool:
    return DEFAULT_POLICY.requires_approval(action, score)


def load_policy(path: str | os.PathLike | None = None) -> Policy:
    """Load a YAML policy. Falls back to the built-in default if absent/unavailable."""
    if path and Path(path).exists() and yaml is not None:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return Policy.from_dict(data)
    return DEFAULT_POLICY
