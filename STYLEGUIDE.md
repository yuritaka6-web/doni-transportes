# Constituição técnica — Doni Transportes

Revisão de arquitetura autorizada pelo autor em 20/11/2026. Esta revisão orienta a migração; não altera a cronologia da implementação anterior.

- Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 e PyJWT; dependências fixadas em `src/api/requirements.txt`.
- SQLite local e nos testes; PostgreSQL persistente na hospedagem gratuita. Nunca guardar o banco em disco efêmero de produção.
- Entidades com colunas tipadas, `Mapped`, `mapped_column`, `ForeignKey` e `relationship`. Consultas com `select`; relacionamentos com `selectinload`; transações explícitas e rollback em falhas.
- Camadas em `src/api/`: schemas, models, database, security, exceptions, notifications e routers. Contrato exportado em `docs/openapi-v2.json`.
- JWT HS256, Bearer, duração de 1 hora, claims `sub`, `email`, `role`, `iat`, `exp`, `iss`, `aud` e `jti`. Papéis ADMIN e MEMBER. Senhas scrypt com salt; nenhuma senha padrão em produção.
- Erros RFC 9457 com `type`, `title`, `status`, `detail`, `instance` e `invalidParams`; HTTP 400/401/403/404/409/422/429 coerentes. Falhas de validação não retornam dados sensíveis.
- Todos os schemas de corpos e respostas são componentes reutilizáveis. Manter JSON camelCase do domínio, UUID, datas e limites do contrato.
- Dados pessoais exigem autenticação para consulta; criação administrativa exige JWT, alteração por ADMIN/MEMBER, exclusão por ADMIN. O formulário público tem endpoint próprio com validação, limite de uso e resposta sem dados de terceiros.
- Orçamento e outbox gravados na mesma transação. E-mail com dados do contato, Reply-To e link WhatsApp. Retentativas sem novo orçamento e sem reenviar após PATCH. Em Render gratuito usar transporte HTTPS autenticado, pois SMTP é bloqueado.
- Credenciais apenas por variáveis de ambiente; `.env`, tokens, hashes, bancos e cópias de dados nunca entram no Git.
- Testes pytest/TestClient com banco isolado: contrato, CRUD, JWT inválido/expirado, RBAC, relacionamento, rollback, persistência, notificação e indisponibilidade do transporte.
