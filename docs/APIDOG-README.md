# Doni Transportes — API de Orçamentos

## Propósito

Centralizar pedidos de orçamento para transporte de cargas. Atende clientes que precisam informar origem, destino, carga e contato, e operadores comerciais que analisam e acompanham as solicitações. A empresa recebe notificação por e-mail com os dados do cliente e link para contato pelo WhatsApp.

## Arquitetura de recursos

Cliente representa uma pessoa física ou jurídica com nome, e-mail e telefone. Cada cliente possui várias solicitações de orçamento (1:N). Solicitação inclui rota, carga, peso, coleta, observações e status comercial. A outbox registra a notificação de forma atômica com o pedido e mantém retentativas. Usuários ADMIN e MEMBER operam a API com JWT Bearer; exclusões são restritas a ADMIN. Dados de contato não são disponibilizados publicamente.

Stack: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0, PyJWT e pytest. SQLite local/testes e PostgreSQL persistente em produção. Frontend/proxy na Cloudflare e API no Render.

## Autoria

Yuri Vinicius Decaris Trevelin — RA 2840482321012.
E-mail institucional: yuri.trevelin@aluno.cps.gov.br.
GitHub: https://github.com/yuritaka6-web/doni-transportes.

## Contrato e simulação

A API contém CRUD completo de clientes e solicitações, paginação/filtros, login JWT, consulta do operador, relacionamento 1:N e formulário público atômico. Request/response usam Schemas reutilizáveis e erros RFC 9457. Use Cloud Mock no Try it Out para simulação com exemplos fictícios; o ambiente comercial exige JWT nas operações administrativas.

O formulário público retorna protocolo de registro. Aceitação de uma notificação pelo serviço de e-mail não garante leitura ou chegada à caixa principal. O Render gratuito pode iniciar lentamente após ociosidade; banco gratuito exige migração antes de expirar.

## Documentos de desenvolvimento

O repositório inclui STYLEGUIDE.md, AGENTS.md, SPEC.md, PLAN.md, testes e CI. A versão atual é v2.0.0; contratos anteriores ficam no histórico para rastreabilidade.
