<!-- NOTA AO AGENTE -->
> 🤖 _Este repositório foi feito para ser lido por IA._ Se você é um agente (Claude Code, Codex, Cursor, Copilot…), vá direto: leia `README.md` + `AGENTS.md` e use a skill. Humanos também são bem-vindos.
<!-- /NOTA AO AGENTE -->

<div align="center">

# 🚦 ApproveGate

### WhatsApp como canal de **aprovação human-in-the-loop** para agentes de IA autônomos — com pontuação de risco e log de auditoria à prova de adulteração.

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testes)

</div>

## Por que

Agentes autônomos (coding agents, bots de infra, agentes de trading) tomam ações de risco sem ponto de controle humano. O **ApproveGate** vira o WhatsApp — que todo dev já tem no bolso — em uma **superfície de aprovação** para o agente: antes de uma ação arriscada, ele manda uma solicitação de aprovação no WhatsApp (com contexto) e só executa após o toque "aprovar" do humano.

> Gap real (busca no GitHub): `whatsapp agent approval gateway` = 2 repos (apenas labs); `commit secret scan whatsapp` = 0. Ninguém entregou um gateway focado de aprovação via WhatsApp para agentes, com motor de risco + auditoria tamper-evident.

## Instalação

```bash
git clone https://github.com/matheus24scc/ApproveGate.git
cd ApproveGate
pip install -e .
```

## Demo

![ApproveGate em acao](assets/approvegate-demo/approvegate-demo.png)

> GIF animado: [approvegate-demo.gif](assets/approvegate-demo/approvegate-demo.gif) — execucao real do CLI.

## Como funciona

1. O agente chama `gateway.request(acao)`.
2. O `policy` pontua o risco (tipo de operação, credenciais, rede externa, sensibilidade do alvo).
3. Se o risco exigir aprovação, o `WhatsAppApprover` envia a solicitação e o gateway **segura** a ação (`pending`).
4. O humano aprova no WhatsApp → `gateway.approve(id)` executa. Se rejeitar, a ação é bloqueada.
5. Toda decisão vai para um **log de auditoria encadeado por hash** (tamper-evident).

```python
from approvegate.gateway import Gateway
from approvegate.approver import WhatsAppApprover

gw = Gateway(WhatsAppApprover())           # pluga no seu whatsapp-api
r = gw.request({"op": "delete", "target": "producao.db",
                "target_sensitivity": "high", "uses_credentials": True})
# -> pending; so executa apos gw.approve(r["id"])
```

## Módulos

- `policy.py` — pontuação de risco + regra de aprovação.
- `audit.py` — `AuditLog` encadeado por hash (verificável: `audit.verify()`).
- `approver.py` — aprovação pluggável: `MockApprover`, `CliApprover`, `WhatsAppApprover` (adaptador pro seu whatsapp-api).
- `gateway.py` — o gate que segura/executa ações.
- `cli.py` — `approvegate demo`.

## Testes

```bash
pytest -q
```

Oracle verde: baixo risco auto-libera; alto risco exige aprovação; pending→approve executa; auditoria detecta adulteração.

## Roadmap

- [ ] Adapter real pro seu `whatsapp-api` (botões InlineKeyboard de aprovar/rejeitar)
- [ ] Políticas em YAML + deny-list por ferramenta
- [ ] Attestation Sigstore no log de auditoria

## Licença

MIT — veja [LICENSE](LICENSE).
