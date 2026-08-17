"""Exemplo: ligar o ApproveGate ao seu whatsapp-api (aprovacao via resposta).

1) Suba o whatsapp-api (github.com/matheus24scc/whatsapp-api).
2) Configure o whatsapp-api para encaminhar mensagens recebidas ao webhook abaixo.
3) Exporte as variaveis e rode este script.

Requisito de integracao (lado whatsapp-api): encaminhar o texto da mensagem
recebida via POST para http://<host>:8080/webhook/whatsapp com {"body": "<texto>"}
ou {"request_code": "AG0001", "decision": "approved"}.
"""
import os
from approvegate.gateway import Gateway
from approvegate.whatsapp import WhatsAppApprover, start_webhook


def main() -> None:
    approver = WhatsAppApprover(
        api_base=os.environ["WHATSAPP_API_BASE"],     # http://localhost:3000
        session_id=os.environ["WHATSAPP_SESSION"],    # "vendas"
        approver_phone=os.environ["APPROVER_PHONE"],  # 5511999999999
    )
    gw = Gateway(approver)
    approver.gateway = gw
    server = start_webhook(approver, host="0.0.0.0", port=8080)
    print("ApproveGate escutando webhook em :8080 — aguardando aprovacoes no WhatsApp...")
    server.serve_forever()


if __name__ == "__main__":
    main()
