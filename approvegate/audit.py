"""ApproveGate — tamper-evident (hash-chained) audit log."""
from __future__ import annotations
import hashlib, json

def _hash(prev: str | None, data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256((prev or "").encode() + payload.encode()).hexdigest()

class AuditLog:
    def __init__(self) -> None:
        self.entries: list[dict] = []
        self._prev: str | None = None

    def append(self, data: dict) -> dict:
        h = _hash(self._prev, data)
        entry = {"seq": len(self.entries) + 1, "data": data, "hash": h, "prev": self._prev}
        self.entries.append(entry)
        self._prev = h
        return entry

    def verify(self) -> bool:
        prev = None
        for e in self.entries:
            if _hash(prev, e["data"]) != e["hash"]:
                return False
            prev = e["hash"]
        return True
