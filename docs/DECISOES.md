# Decisões arquiteturais

## ADR-001 — ORM e compatibilidade do banco

Drizzle ORM com adaptador nativo node:sqlite, versão exata no package-lock. Essa integração usa release candidate; a escolha evita instalar outro driver nativo e mantém o Node 24 já usado pelo projeto. Consultas e gravações de domínio, fila e autenticação passam pelo ORM. SQL direto fica nas migrações versionadas e em testes de diagnóstico.

O modelo da Parte 1 guarda atributos em JSON, com id e clienteId relacionais. Esse modelo híbrido foi preservado para migrar sem apagar pedidos. Usuários e sessões têm colunas individuais. Uma evolução futura pode normalizar os atributos de carga e contato, com migração específica. Não se afirma que o banco atual seja totalmente normalizado.

## ADR-002 — Autenticação por sessão

Sessão opaca de 256 bits, hash SHA-256 no banco, cookie HttpOnly/SameSite=Strict e validade de 8 horas. A senha usa scrypt com salt aleatório. A conta inicial é criada localmente, sem senha padrão e sem endpoint público de registro. ADMIN pode gerir; LEITOR pode consultar. GETs de domínio exigem sessão. Os POSTs de cadastro/solicitação continuam públicos para atender o site.

Em NODE_ENV=production o cookie usa Secure e prefixo __Host-. Isso exige HTTPS em uma implantação futura. Não foi usado JWT porque a revogação imediata e o uso do painel na mesma origem favorecem sessões persistentes. Login limita falhas por IP; mutações validam Origin quando presente. O limite em memória é adequado ao processo local, mas não substitui proteção distribuída em produção.

## ADR-003 — Dois contratos preservados

`docs/openapi.json` é a versão 1.0 da Parte 1, já publicada. `docs/openapi-v1.1.json` documenta a Parte 2, com 13 operações, autenticação e novos erros. O backend usa v1.1 para validação e a disponibiliza em `/openapi.json`; `/openapi-v1.json` preserva o contrato anterior. O Cloud Mock da Parte 1 é uma simulação sem autenticação real e não comprova as regras da Parte 2.

## ADR-004 — E-mail com outbox

Pedido e notificação são gravados na mesma transação ORM. O worker SMTP opera após o commit e retenta falhas; nunca expõe a senha SMTP. A mensagem contém os contatos, a carga, Reply-To e link para WhatsApp do cliente. ENVIADO significa aceitação pelo SMTP. Semântica pelo menos uma vez pode duplicar mensagens após interrupção entre aceite e gravação do status.

## Limites conhecidos

Sem hospedagem pública do backend, recuperação de senha, MFA, paginação por cursor ou monitoramento externo. O servidor continua restrito a loopback. Autenticação é funcional, mas implantação pública ainda requer HTTPS, proxy confiável, armazenamento persistente, backups, proteção distribuída contra abuso e política de dados pessoais.
