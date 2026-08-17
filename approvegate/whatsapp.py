"""ApproveGate — real WhatsApp adapter + return-webhook (plugs into your whatsapp-api).

Contract
--------
- The approver SENDS the approval request to a human via your whatsapp-api
  (POST {api_base}/api/send/text with {"sessionId","to","text"}).
- The human replies with the request code, e.g. "APROVAR AG0001" / "REJEITAR AG0001".
- Your whatsapp-api must forward incoming messages to ApproveGate's webhook
  (POST {webhook_url}/webhook/whatsapp with {"body": "<text>"} or
  {"request_code":"AG0001","decision":"approved"}). ApproveGate then resolves the request.
Numbers/phones come from config (env) — never hardcoded.
"""
from __future__ import annotations
import json
import re
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .approver import Approver

DECISION_WORDS = {
    "aprovar": "approved", "approve": "approved", "sim": "approved", "yes": "approved", "y": "approved",
    "rejeitar": "rejected", "reject": "rejected", "nao": "rejected", "não": "rejected", "no": "rejected", "n": "rejected",
}
_CODE_RE = re.compile(r"(APROVAR|REJEITAR|APPROVE|REJECT)\s*(AG\d+)", re.IGNORECASE)


def _code_for(rid: int) -> str:
    return f"AG{rid:04d}"


def _parse_reply(text: str):
    m = _CODE_RE.search(text or "")
    if not m:
        return None, None
    decision = "approved" if m.group(1).upper().startswith("AP") else "rejected"
    return m.group(2).upper(), decision


class WhatsAppApprover(Approver):
    def __init__(self, send_fn=None, gateway=None, api_base=None, session_id=None,
                 approver_phone=None, mode="text", timeout=10):
        self.send_fn = send_fn
        self.gateway = gateway
        self.api_base = api_base.rstrip("/") if api_base else None
        self.session_id = session_id
        self.approver_phone = approver_phone
        self.mode = mode
        self.timeout = timeout
        self._codes = {}  # code -> rid

    def request_approval(self, action: dict, score: int) -> str:
        # async: the human decides later (via webhook). Gateway calls register().
        return "pending"

    def register(self, rid: int, action: dict, score: int) -> None:
        code = _code_for(rid)
        self._codes[code] = rid
        text = (f"🛡️ ApproveGate — solicitacao {code}\n"
                f"Acao: {action.get('op')} | Alvo: {action.get('target')} | Risco: {score}\n"
                f"Responda 'APROVAR {code}' ou 'REJEITAR {code}'.")
        self._send(text)

    def _send(self, text: str) -> None:
        if self.send_fn:
            self.send_fn(self.approver_phone, text)
            return
        if self.api_base and self.session_id and self.approver_phone:
            payload = json.dumps({"sessionId": self.session_id, "to": self.approver_phone,
                                  "text": text}).encode()
            req = urllib.request.Request(f"{self.api_base}/api/send/text", data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=self.timeout).close()
            return
        # safe default (demo / no live API configured): just print
        print(f"[WhatsApp] ⚠️ aprovacao solicitada: {text.splitlines()[0]}")

    def resolve(self, code: str, decision: str):
        rid = self._codes.pop(code, None)
        if rid is None or self.gateway is None:
            return None
        if decision == "approved":
            return self.gateway.approve(rid)
        return self.gateway.reject(rid)


def make_handler(approver):
    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw or b"{}")
            except Exception:
                data = {}
            code, decision = None, None
            if "request_code" in data or "code" in data:
                code = str(data.get("request_code") or data.get("code") or "").upper()
                decision = data.get("decision")
                if decision not in ("approved", "rejected"):
                    decision = DECISION_WORDS.get(str(decision or "").lower())
            elif "body" in data:
                code, decision = _parse_reply(data.get("body"))
            if code and decision:
                approver.resolve(code, decision)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "code": code, "decision": decision}).encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "unrecognized payload"}).encode())

        def do_POST(self):
            if self.path.rstrip("/") == "/webhook/whatsapp":
                self._handle()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *a):
            pass

    return Handler


def start_webhook(approver, host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(approver))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
