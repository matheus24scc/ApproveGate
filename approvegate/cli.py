"""ApproveGate CLI — demo: WhatsApp human-in-the-loop for agents."""
from __future__ import annotations
import argparse
from .gateway import Gateway
from .approver import MockApprover, WhatsAppApprover

def demo() -> None:
    print("=== ApproveGate: WhatsApp como canal de aprovacao p/ agentes ===\n")
    gw = Gateway(WhatsAppApprover())
    # 1) acao de baixo risco: auto-liberada
    r1 = gw.request({"op": "read", "target": "relatorio.txt"})
    print(f"[agente] quer 'read' -> {r1['status']} ({r1['result']})\n")
    # 2) acao de ALTO risco: segura p/ aprovacao via WhatsApp
    r2 = gw.request({"op": "delete", "target": "producao.db", "target_sensitivity": "high",
                     "uses_credentials": True})
    print(f"[agente] quer 'delete producao.db' (risco {r2 and gw.audit.entries[-1]['data']['score']}) "
          f"-> {r2['status']} (aguardando humano)\n")
    # 3) humano aprova no WhatsApp -> gateway executa
    rid = r2["id"]
    r3 = gw.approve(rid)
    print(f"[humano aprovou no WhatsApp] -> {r3['status']} ({r3['result']})\n")
    print(f"Log de auditoria intacto (hash-chain): {gw.audit.verify()}")

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="approvegate", description="Agent action approval gateway (WhatsApp HITL).")
    ap.add_argument("cmd", nargs="?", default="demo", choices=["demo"])
    args = ap.parse_args(argv)
    if args.cmd == "demo":
        demo()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
