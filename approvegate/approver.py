"""ApproveGate — pluggable human-in-the-loop approvers (incl. WhatsApp)."""
from __future__ import annotations
from abc import ABC, abstractmethod

class Approver(ABC):
    @abstractmethod
    def request_approval(self, action: dict, score: int) -> str:
        """Return 'approved', 'rejected' or 'pending'."""

class MockApprover(Approver):
    def __init__(self, decision: str) -> None:
        self.decision = decision
    def request_approval(self, action, score):
        return self.decision

class CliApprover(Approver):
    def request_approval(self, action, score):
        ans = input(f"Approve (risk {score}) {action.get('op')}? [y/N] ").lower()
        return "approved" if ans.startswith("y") else "rejected"

class WhatsAppApprover(Approver):
    """Sends an approval request to a human via WhatsApp (plugs into your whatsapp-api)."""
    def __init__(self, send_fn=None) -> None:
        self.send_fn = send_fn or (lambda action, score: print(
            f"[WhatsApp] ⚠️ aprovacao solicitada: {action.get('op')} (risco {score})"))
    def request_approval(self, action, score):
        self.send_fn(action, score)
        return "pending"  # real flow waits for the human's tap
