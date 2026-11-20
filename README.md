# Doni Transportes — API REST e painel comercial

Projeto acadêmico para cadastrar contatos e solicitações de cotação de frete. O site salva o pedido e notifica a empresa por e-mail com os dados da carga, Reply-To e link para o WhatsApp do cliente. Operadores autenticados acompanham o atendimento no painel.

## Entregas

- [Repositório](https://github.com/yuritaka6-web/doni-transportes)
- [Parte 1: documentação pública Apidog](https://share.apidog.com/9fe351b6-4c9d-4d1e-b34f-1865dbc6a4c6)
- [Parte 2: especificação](specs/001-parte2/spec.md), [plano](specs/001-parte2/plan.md) e [tarefas](specs/001-parte2/tasks.md)
- [Organização e autoria](docs/EQUIPE.md)
- [Desenvolvimento com IA e SDD](docs/IA-SDD.md)
- [Decisões arquiteturais e limitações](docs/DECISOES.md)

## Executar

Requisito: Node.js **24+** e npm. SQLite não precisa de servidor separado.

```sh
git clone https://github.com/yuritaka6-web/doni-transportes.git
cd doni-transportes
npm ci
```

Copie `.env.example` para `.env` somente se o arquivo ainda não existir. No PowerShell: `Copy-Item .env.example .env`. Preserve configurações existentes.

```sh
npm run admin:create -- seu-email@example.com
npm start
```

O comando pede nome e senha de 12 a 128 caracteres, com digitação oculta. Não existe conta ou senha padrão.

| Endereço local | Finalidade |
| --- | --- |
| http://127.0.0.1:3000 | Site |
| http://127.0.0.1:3000/orcamento.html | Formulário público |
| http://127.0.0.1:3000/admin.html | Painel comercial |
| http://127.0.0.1:3000/openapi.json | Contrato real v1.1 |

## Autenticação

| Rotas | Acesso |
| --- | --- |
| POST clientes e solicitações | Público, para o formulário |
| GET clientes e solicitações | ADMIN ou LEITOR |
| PATCH/DELETE clientes e solicitações | ADMIN |
| POST /api/v1/auth/login | Credenciais e limite de tentativas |
| GET /api/v1/auth/me | Sessão válida |
| POST /api/v1/auth/logout | Revoga sessão; idempotente |

Senhas: scrypt com salt aleatório. Sessões: token opaco de 256 bits, com SHA-256 persistido, cookie HttpOnly/SameSite=Strict, validade de 8 horas. Não é JWT. Em NODE_ENV=production, o cookie usa Secure e prefixo __Host-, exigindo HTTPS. Login aceita cinco tentativas em 15 minutos por IP; sucesso reinicia o contador. Os POSTs públicos têm limite de 30 por minuto por IP. Os limites são em memória do processo.

## ORM e banco

Drizzle ORM com adaptador nativo node:sqlite. A integração nativa usa versão release candidate, fixada no lockfile e testada. Veja a [documentação oficial](https://orm.drizzle.team/docs/sqlite/connect-node-sqlite).

Modelos em `src/db/schema.mjs`, consultas em `src/db/database.mjs`, migrações aditivas em `migrations/`. O banco `data/doni.sqlite` é criado automaticamente. Migrações preservam o banco da Parte 1. Dados de domínio continuam em JSON, com id e clienteId relacionais; usuários/sessões têm colunas próprias. Esse modelo híbrido não é totalmente normalizado. O acesso a domínio, fila, usuários e sessões usa ORM; SQL direto é reservado às migrações e testes de diagnóstico.

Pedido e notificação são gravados na mesma transação ORM. O worker processa a outbox após o commit. Sem SMTP, pedidos ficam salvos e e-mails pendentes. Falhas recebem reenvio progressivo. ENVIADO significa aceite SMTP, não chegada na caixa de entrada. Uma interrupção após aceite pode duplicar mensagens. PATCH não reenvia e-mail.

## Configurar e-mail

Preencha localmente SMTP_USER, SMTP_PASS e MAIL_FROM no `.env`, conforme `.env.example`. COMPANY_EMAIL define o destinatário fixo. Gmail pode ser o servidor de envio; use uma senha de app e siga a [orientação oficial do Google](https://support.google.com/accounts/answer/185833). Reinicie após alterar o ambiente. Nunca publique `.env`; ele contém credenciais.

## Contratos

- `docs/openapi.json`: v1.0 da Parte 1; 10 operações e 20 schemas; publicação preservada.
- `docs/openapi-v1.1.json`: Parte 2; 13 operações e 23 schemas, com autenticação e erros 401/403/429. Fonte dos validadores da API real.
- `/openapi-v1.json`: contrato inicial servido localmente.
- `docs/README.md`: documento inicial publicado no Apidog.

O Cloud Mock representa a Parte 1; não valida autenticação real nem persistência. O mock local roda com `npm run mock` em http://127.0.0.1:3001 e não envia e-mails. O Design-First anterior à implementação da Parte 1 não foi comprovado retroativamente. A especificação da evolução da Parte 2 foi escrita antes de suas alterações de código.

## Verificação

```sh
npm run check:contract
npm test
npm audit --omit=dev --audit-level=high
```

A suíte tem 12 testes de integração: CRUD, validações, paginação/filtros, relação 1:N, persistência, autenticação, papéis, sessão expirada/revogada, bloqueio de login, migração de banco legado, rollback e e-mail simulado. Não envia mensagens reais. O workflow `.github/workflows/ci.yml` repete os checks no GitHub; confira a aba Actions para saber o resultado remoto.

## Estrutura

```text
specs/001-parte2/      especificação, plano e tarefas
src/db/               modelos e repositório Drizzle
src/auth.mjs          senha, sessão e limites
migrations/           migrações SQL versionadas
server.mjs            HTTP e autorização das rotas
validation.mjs        validação derivada do OpenAPI
mail.mjs              template e worker da outbox
admin.html / admin.js painel comercial
orcamento.*           formulário público
scripts/              criação local do administrador e checks
tests/                testes de integração
docs/                 contratos e decisões técnicas
.github/workflows/    CI
```

## Limites e autoria

Versão acadêmica local, escutando apenas em loopback. O domínio público não recebeu este backend; GitHub Pages não executa Node.js. Implantação pública requer HTTPS, armazenamento persistente, backups, proxy confiável, proteção distribuída contra abuso e política de dados pessoais. Não há recuperação de senha, MFA, pagamentos ou GPS. Faça backup do banco antes de atualizar um ambiente com dados reais.

**Yuri Vinicius Decaris Trevelin — RA 2840482321012 — yuri.trevelin@aluno.cps.gov.br.** Desenvolvimento com assistência do Codex, conforme o registro de IA e SDD.
