# Doni Transportes — API de Orçamentos

API REST para cadastrar clientes e gerenciar solicitações de transporte. O site registra orçamento em banco persistente e notifica a empresa com os dados de contato, Reply-To e link de WhatsApp. O painel comercial permite acompanhar pedidos e atualizar seu status.

**Autor:** Yuri Vinicius Decaris Trevelin — RA 2840482321012 — yuri.trevelin@aluno.cps.gov.br.

- Site: https://donitransportes.com.br
- Documentação: https://share.apidog.com/9fe351b6-4c9d-4d1e-b34f-1865dbc6a4c6
- Contrato: [OpenAPI v2](docs/openapi-v2.json)
- Governança: [STYLEGUIDE](STYLEGUIDE.md), [AGENTS](AGENTS.md), [SPEC](SPEC.md), [PLAN](PLAN.md)

## Arquitetura

Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 e JWT HS256/RBAC (ADMIN/MEMBER). SQLite local/testes; PostgreSQL persistente no Render. Cliente possui várias solicitações com ForeignKey/relationship. selectinload evita N+1. Orçamento e outbox usam a mesma transação. O site/proxy ficam na Cloudflare; regras de negócio e persistência executam em Python. Node/Wrangler é apenas ferramenta de implantação dos assets/proxy.

## Executar

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r src/api/requirements.txt
Copy-Item .env.example .env
.venv/Scripts/python scripts/manage.py create-admin
.venv/Scripts/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000, /admin.html e /docs. Não existe senha padrão. Para importar dados/conta anteriores, use `scripts/manage.py import-legacy --source caminho/do/banco.sqlite`. O importador preserva UUIDs e hashes, é idempotente e não altera a origem nem importa sessões.

## Segurança

POST /api/v1/auth/login recebe email/password e devolve accessToken/tokenType/expiresIn/user. Use Authorization: Bearer nas operações administrativas. JWT dura uma hora; o painel guarda o token somente na memória. Sair o remove do navegador; tokens emitidos continuam válidos até expirar. MEMBER consulta/cria/edita; ADMIN também exclui. O formulário público usa POST /api/v1/orcamentos/publico, com contato/pedido/outbox atômicos. Erros RFC 9457.

## Verificação

```powershell
.venv/Scripts/python -m pytest
.venv/Scripts/python scripts/export_contract.py
```

[Validação](docs/VERIFICACAO-PARTE2.md), [decisões](docs/DECISOES.md), [processo com IA](docs/IA-SDD.md), [implantação](docs/IMPLANTACAO.md).

## Notificações e hospedagem

A API HTTPS do Resend contorna o bloqueio SMTP do Render gratuito; a chave fica somente no servidor. O remetente inicial onboarding@resend.dev entrega exclusivamente ao e-mail verificado do responsável. Para outros destinatários, verifique um domínio no provedor. SMTP TLS está disponível para ambientes compatíveis. Outbox usa lease/backoff e não reenvia por PATCH. Aceitação pelo fornecedor não garante leitura ou caixa principal; o Resend usa chave de idempotência por protocolo durante 24 horas para reduzir duplicações; fora dessa janela, uma falha ambígua ainda pode duplicar a notificação.

A API gratuita pode levar cerca de um minuto para iniciar após ociosidade. O PostgreSQL gratuito expira em 30 dias, exigindo exportação/migração antes do vencimento. Nenhum banco fica no disco efêmero. Credenciais e bootstrap não entram no Git. A implementação Node anterior permanece no histórico; a API atual é Python.
