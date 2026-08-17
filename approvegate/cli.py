"""ApproveGate CLI — demo: WhatsApp human-in-the-loop for agents."""
from __future__ import annotations
import argparse
from .gateway import Gateway
from .approver import MockApprover, WhatsAppApprover

def demo() -> None:
    print("=== ApproveGate: WhatsApp como canal de aprovacao HITL p/ agentes ===\n")
    gw = Gateway(WhatsAppApprover())
    from .mcp import handle_message
    # 1) baixo risco: auto-liberada
    r1 = gw.request({"op": "read", "target": "relatorio.txt"})
    print(f"[agente] quer 'read' -> {r1['status']} ({r1['result']})")
    # 2) ALTO risco: segura p/ aprovacao via WhatsApp
    r2 = gw.request({"op": "delete", "target": "producao.db", "target_sensitivity": "high",
                     "uses_credentials": True})
    score = gw.audit.entries[-1]["data"]["score"]
    print(f"[agente] quer 'delete producao.db' (risco {score}) -> {r2['status']} (aguardando humano)")
    # 3) humano aprova no WhatsApp -> executa
    r3 = gw.approve(r2["id"])
    print(f"[humano aprovou no WhatsApp] -> {r3['status']} ({r3['result']})")
    # 4) ATESTADO CRIPTOGRAFICO (contextlock-inspired): cada decisao assinada
    print(f"[attestation] decisoes assinadas (DSSE/Ed25519) verificadas: {gw.signed_verify_all()}")
    # 5) MCP SERVER (serac-inspired): expoe request_approval p/ qualquer agente MCP
    tools = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, gw)["result"]["tools"]
    print(f"[mcp] tools expostas: {[t['name'] for t in tools]}")
    print(f"\nLog de auditoria intacto (hash-chain): {gw.audit.verify()}")
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
