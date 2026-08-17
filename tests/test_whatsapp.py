"""Testes do adapter real de WhatsApp + webhook de retorno."""
import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from approvegate.gateway import Gateway
from approvegate.whatsapp import WhatsAppApprover, start_webhook


def test_whatsapp_pending_and_resolve():
    sent = []
    wa = WhatsAppApprover(send_fn=lambda phone, text: sent.append(text), gateway=None)
    gw = Gateway(wa)
    wa.gateway = gw
    r = gw.request({"op": "delete", "target": "db", "target_sensitivity": "high", "uses_credentials": True})
    assert r["status"] == "pending"
    assert sent and "AG0001" in sent[0]
    res = wa.resolve("AG0001", "approved")
    assert res["status"] == "executed"


def test_webhook_json_contract():
    sent = []
    wa = WhatsAppApprover(send_fn=lambda p, t: sent.append(t), gateway=None)
    gw = Gateway(wa)
    wa.gateway = gw
    gw.request({"op": "exec", "target": "x", "uses_credentials": True, "external_network": True})
    server = start_webhook(wa, host="127.0.0.1", port=0)
    port = server.server_address[1]
    data = json.dumps({"request_code": "AG0001", "decision": "approved"}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/webhook/whatsapp", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        out = json.loads(resp.read())
    assert out["ok"] is True
    assert gw.audit.entries[-1]["data"]["executed"] is True
    server.shutdown()


def test_webhook_text_reply():
    sent = []
    wa = WhatsAppApprover(send_fn=lambda p, t: sent.append(t), gateway=None)
    gw = Gateway(wa)
    wa.gateway = gw
    gw.request({"op": "drop", "target": "t", "uses_credentials": True})
    server = start_webhook(wa, host="127.0.0.1", port=0)
    port = server.server_address[1]
    data = json.dumps({"body": "REJEITAR AG0001"}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/webhook/whatsapp", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        out = json.loads(resp.read())
    assert out["decision"] == "rejected"
    assert gw.audit.entries[-1]["data"]["executed"] is False
    server.shutdown()


def test_real_http_send_to_fake_api():
    received = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            ln = int(self.headers.get("Content-Length", 0))
            received["body"] = json.loads(self.rfile.read(ln))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    wa = WhatsAppApprover(api_base=f"http://127.0.0.1:{port}", session_id="s1",
                          approver_phone="5511999999999", gateway=None)
    gw = Gateway(wa)
    wa.gateway = gw
    gw.request({"op": "delete", "target": "db", "uses_credentials": True})
    assert received and received["body"]["to"] == "5511999999999"
    assert "AG0001" in received["body"]["text"]
    srv.shutdown()
