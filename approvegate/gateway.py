"""ApproveGate — the approval gateway that gates agent actions."""
from __future__ import annotations
from .policy import risk_score, requires_approval
from .audit import AuditLog
from .attest import sign, verify

class Gateway:
    def __init__(self, approver) -> None:
        self.approver = approver
        self.audit = AuditLog()
        self.signed = []          # contextlock-inspired: signed envelope per decision
        self.pending: dict[int, dict] = {}
        self._id = 0

    def _record(self, rec: dict) -> None:
        self.audit.append(rec)
        self.signed.append(sign({**rec, "nonce": len(self.signed)}))

    def _exec(self, action, handler):
        return handler(action) if handler else f"executed:{action.get('op')}"

    def request(self, action: dict, handler=None) -> dict:
        self._id += 1
        rid = self._id
        score = risk_score(action)
        base = {"id": rid, "op": action.get("op"), "score": score}
        if not requires_approval(action, score):
            result = self._exec(action, handler)
            self._record({**base, "decision": "auto-allowed", "executed": True})
            return {"id": rid, "status": "executed", "result": result}
        decision = self.approver.request_approval(action, score)
        if decision == "approved":
            result = self._exec(action, handler)
            self._record({**base, "decision": "approved", "executed": True})
            return {"id": rid, "status": "executed", "result": result}
        if decision == "rejected":
            self._record({**base, "decision": "rejected", "executed": False})
            return {"id": rid, "status": "blocked", "result": None}
        # pending: hold for async human approval
        self.pending[rid] = {"action": action, "score": score, "handler": handler}
        self._record({**base, "decision": "pending", "executed": False})
        return {"id": rid, "status": "pending", "result": None}

    def approve(self, rid: int, handler=None) -> dict:
        req = self.pending.pop(rid, None)
        if req is None:
            return {"id": rid, "status": "not-pending"}
        result = self._exec(req["action"], handler or req.get("handler"))
        self._record({"id": rid, "op": req["action"].get("op"),
                      "score": req["score"], "decision": "approved-late", "executed": True})
        return {"id": rid, "status": "executed", "result": result}

    def reject(self, rid: int) -> dict:
        if rid in self.pending:
            self.pending.pop(rid)
            self._record({"id": rid, "decision": "rejected-late", "executed": False})
            return {"id": rid, "status": "blocked"}
        return {"id": rid, "status": "not-pending"}

    def signed_verify_all(self) -> bool:
        """Verify every signed approval envelope (DSSE) is intact + authentic."""
        return all(verify(e) for e in self.signed)
