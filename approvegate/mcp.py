"""ApproveGate — minimal MCP server (serac-inspired) so any agent can request approval."""
from __future__ import annotations
import json, sys, os
from .gateway import Gateway
from .approver import MockApprover

SERVER_INFO = {"name": "ApproveGate", "version": "0.1.0"}

def handle_message(msg: dict, gw: Gateway) -> dict | None:
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": SERVER_INFO}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [{
            "name": "request_approval",
            "description": "Request human approval for an agent action via ApproveGate.",
            "inputSchema": {"type": "object", "properties": {"action": {"type": "object"}},
                            "required": ["action"]}}]}}
    if method == "tools/call":
        name = msg["params"]["name"]
        if name == "request_approval":
            action = msg["params"]["arguments"]["action"]
            res = gw.request(action)
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": json.dumps(res)}]}}
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "unknown tool"}}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}

def serve(gw: Gateway | None = None) -> None:
    gw = gw or Gateway(MockApprover("pending"))
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        resp = handle_message(msg, gw)
        if resp:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    serve()
