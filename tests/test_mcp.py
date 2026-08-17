"""Testes do MCP server (serac-inspired) — request_approval exposto via MCP."""
import json
from approvegate.gateway import Gateway
from approvegate.approver import MockApprover
from approvegate.mcp import handle_message

def test_mcp_initialize():
    r = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, Gateway(MockApprover("pending")))
    assert r["result"]["protocolVersion"] == "2024-11-05"
    assert r["result"]["serverInfo"]["name"] == "ApproveGate"

def test_mcp_tools_list():
    r = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, Gateway(MockApprover("pending")))
    names = [t["name"] for t in r["result"]["tools"]]
    assert "request_approval" in names

def test_mcp_request_approval_executed():
    gw = Gateway(MockApprover("approved"))
    msg = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
           "params": {"name": "request_approval",
                      "arguments": {"action": {"op": "delete", "target": "db",
                                               "target_sensitivity": "high", "uses_credentials": True}}}}
    r = handle_message(msg, gw)
    assert json.loads(r["result"]["content"][0]["text"])["status"] == "executed"

def test_mcp_request_approval_pending():
    gw = Gateway(MockApprover("approved"))  # approved so high-risk executes; use pending
    gw = Gateway(MockApprover("pending"))
    msg = {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
           "params": {"name": "request_approval",
                      "arguments": {"action": {"op": "exec", "target": "x",
                                               "uses_credentials": True, "external_network": True}}}}
    r = handle_message(msg, gw)
    assert json.loads(r["result"]["content"][0]["text"])["status"] == "pending"
