"""Smoke test end-to-end do ApproveGate (uso real de cada modulo)."""
from __future__ import annotations
import sys, json, base64, threading, urllib.request, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from approvegate.gateway import Gateway
from approvegate.approver import MockApprover
from approvegate.whatsapp import WhatsAppApprover, start_webhook
from approvegate.mcp import handle_message
from approvegate.policy import load_policy
from approvegate.attest import sign, verify
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def chk(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    return bool(cond)


def main() -> int:
    results = []
    A = results.append

    # Gateway com diversos approvers
    gw = Gateway(MockApprover("approved"))
    A(chk("low-risk auto-allowed", gw.request({"op": "read"})["status"] == "executed"))
    A(chk("high-risk approved executes",
          gw.request({"op": "delete", "target_sensitivity": "high", "uses_credentials": True})["status"] == "executed"))
    gw = Gateway(MockApprover("rejected"))
    A(chk("high-risk rejected blocked",
          gw.request({"op": "drop", "uses_credentials": True})["status"] == "blocked"))
    gw = Gateway(MockApprover("pending"))
    r = gw.request({"op": "exec", "uses_credentials": True, "external_network": True})
    A(chk("pending->approve executes", gw.approve(r["id"])["status"] == "executed"))
    gw = Gateway(MockApprover("pending"))
    r = gw.request({"op": "exec", "uses_credentials": True})
    A(chk("pending->reject blocked", gw.reject(r["id"])["status"] == "blocked"))

    # Fluxo WhatsApp real (api falsa + webhook)
    received = {}
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0)); b = self.rfile.read(n)
            received["body"] = json.loads(b); self.send_response(200)
            self.end_headers(); self.wfile.write(b"{}")
        def log_message(self, *a): pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    wa = WhatsAppApprover(api_base=f"http://127.0.0.1:{port}", session_id="s1", approver_phone="5511999999999")
    gw = Gateway(wa); wa.gateway = gw
    r = gw.request({"op": "delete", "target": "db", "uses_credentials": True})
    A(chk("whatsapp request -> pending", r["status"] == "pending"))
    A(chk("whatsapp-api recebeu POST /api/send/text",
          bool(received) and received["body"]["to"] == "5511999999999" and "AG0001" in received["body"]["text"]))
    wh = start_webhook(wa, host="127.0.0.1", port=0); wport = wh.server_address[1]
    data = json.dumps({"body": "APROVAR AG0001"}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{wport}/webhook/whatsapp", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        out = json.loads(resp.read())
    A(chk("webhook resolveu aprovacao (executed)", gw.audit.entries[-1]["data"]["executed"] is True and out["decision"] == "approved"))
    wh.shutdown(); srv.shutdown()

    # MCP
    gw = Gateway(MockApprover("pending"))
    A(chk("mcp initialize", handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, gw)["result"]["serverInfo"]["name"] == "ApproveGate"))
    tools = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, gw)["result"]["tools"]
    A(chk("mcp expoe request_approval", any(t["name"] == "request_approval" for t in tools)))
    res = handle_message({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "request_approval", "arguments": {"action": {"op": "delete", "target_sensitivity": "high", "uses_credentials": True}}}},
        Gateway(MockApprover("approved")))
    A(chk("mcp tools/call (approved) executa", json.loads(res["result"]["content"][0]["text"])["status"] == "executed"))

    # Policy YAML
    y = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    y.write("threshold: 30\nweights:\n  read: 10\ndeny_list:\n  - op: drop\n"); y.close()
    pol = load_policy(y.name)
    A(chk("policy yaml threshold", pol.threshold == 30))
    A(chk("policy yaml deny op=drop", pol.requires_approval({"op": "drop"}, 5) is True))
    A(chk("policy yaml peso read=10", pol.risk_score({"op": "read"}) == 10))
    A(chk("gateway usa policy", Gateway(MockApprover("approved"), policy=pol)
          .request({"op": "read", "uses_credentials": True, "external_network": True})["status"] == "executed"))

    # Attestation
    env = sign({"id": 1, "op": "delete", "decision": "approved"})
    A(chk("attest sign/verify roundtrip", verify(env) is True))
    bad = json.loads(json.dumps(env)); bad["payload"] = base64.b64encode(b'{"id":1,"decision":"rejected"}').decode()
    A(chk("attest tamper detectado", verify(bad) is False))
    gw = Gateway(MockApprover("approved"))
    gw.request({"op": "read"}); gw.request({"op": "delete", "target_sensitivity": "high", "uses_credentials": True})
    A(chk("gateway signed_verify_all True", gw.signed_verify_all() is True))
    gw.signed[0]["signatures"][0]["sig"] = base64.b64encode(b"x" * 64).decode()
    A(chk("gateway signed_verify_all False apos adulterar", gw.signed_verify_all() is False))

    # Audit tamper-evident
    gw = Gateway(MockApprover("approved"))
    gw.request({"op": "read"}); gw.request({"op": "delete", "target_sensitivity": "high", "uses_credentials": True})
    A(chk("audit.verify True", gw.audit.verify() is True))
    gw.audit.entries[0]["data"]["op"] = "HACKED"
    A(chk("audit.verify False apos adulterar", gw.audit.verify() is False))

    fails = [i for i, o in enumerate(results) if not o]
    print(f"\nSMOKE ApproveGate: {len(results)-len(fails)}/{len(results)} passaram" +
          (f" | FALHAS indices: {fails}" if fails else " | TODOS OK"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
