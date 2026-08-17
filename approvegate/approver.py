"""ApproveGate — pluggable human-in-the-loop approvers (incl. WhatsApp)."""
from __future__ import annotations
from abc import ABC, abstractmethod


class Approver(ABC):
    @abstractmethod
    def request_approval(self, action: dict, score: int) -> str:
        """Return 'approved', 'rejected' or 'pending'."""

    def register(self, rid: int, action: dict, score: int) -> None:
        """Called by the gateway when a request is held as 'pending'.

        Async approvers (e.g. WhatsApp) use this to dispatch the request to the
        human and remember how to resolve it later. Sync approvers ignore it.
        """
        return None


class MockApprover(Approver):
    def __init__(self, decision: str) -> None:
        self.decision = decision

    def request_approval(self, action, score):
        return self.decision


class CliApprover(Approver):
    def request_approval(self, action, score):
        ans = input(f"Approve (risk {score}) {action.get('op')}? [y/N] ").lower()
        return "approved" if ans.startswith("y") else "rejected"
