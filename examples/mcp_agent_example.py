"""Exemplo: um 'agente' usa o ApproveGate via MCP (tool request_approval).

Em producao, o agente se conectaria a um servidor MCP (approvegate.mcp:serve).
Aqui reproduzimos a chamada da tool para ilustrar a integracao sem rede.
"""
from approvegate.gateway import Gateway
from approvegate.approver import MockApprover
from approvegate.mcp import handle_message


def agent_decide(gw: Gateway, action: dict) -> dict:
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "request_approval", "arguments": {"action": action}}}
    return handle_message(msg, gw)


if __name__ == "__main__":
    gw = Gateway(MockApprover("pending"))
    print(agent_decide(gw, {"op": "delete", "target": "producao.db",
                            "target_sensitivity": "high", "uses_credentials": True}))
