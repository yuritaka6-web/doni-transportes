# Especificação — API Doni Transportes v2

Evolução autorizada em 20/11/2026 para alinhar a stack à prática de FastAPI, SQLAlchemy e JWT. Base de domínio: `docs/openapi.json`. Implementação anterior registrada no Git; esta especificação não constitui prova retroativa de Design-First.

## Domínio e contratos

Cliente possui nome (2–120), email (até 254), telefone brasileiro E.164 e tipo PF/PJ. Solicitação pertence a um cliente (1:N), com origem/destino (cidade e UF), descrição de carga (10–2000), peso (0,01–30000 kg), data de coleta, observações opcionais (até 1000), status e situação de e-mail. Servidor atribui UUID, datas e status iniciais.

CRUD completo em `/api/v1/clientes` e `/api/v1/solicitacoes-orcamento`: POST 201/Location, GET paginado 200, GET/PATCH individual 200/404, DELETE 204/404. Filtros validados; cliente vinculado não pode ser excluído (409). Campos extras, PATCH vazio e null indevido retornam 422. JSON malformado retorna 400. Exclusão ADMIN; consulta/criação/alteração ADMIN ou MEMBER.

`POST /api/v1/orcamentos/publico` recebe contato e carga juntos, sem autenticação. Valida tudo antes de persistir, limita abuso, grava cliente/pedido/outbox atomicamente e retorna protocolo. Não permite leitura pública dos contatos.

`POST /api/v1/auth/login` recebe email/password e retorna accessToken/tokenType/expiresIn/user. `GET /api/v1/auth/me` valida JWT e retorna usuário público. Token ausente/inválido/expirado: 401; papel insuficiente: 403. Claims verificadas e segredo forte obrigatório em produção. Painel guarda token apenas em memória e exige novo login após recarregar.

`GET /api/v1/clientes/{id}/solicitacoes-orcamento` demonstra relação ORM 1:N e eager loading. Banco local SQLite; produção PostgreSQL. Migração do banco antigo por comando explícito, preservando IDs, contatos, pedidos e hashes compatíveis; sem importar sessões antigas ou reenviar notificações já enviadas.

## Notificações e implantação

Outbox com captura dos dados no momento do envio. O e-mail empresarial inclui contato, Reply-To e link wa.me do cliente. Sucesso de persistência não afirma entrega na caixa de entrada. Falhas ficam pendentes para retentativa com lease e backoff. Transporte local SMTP TLS; produção gratuita HTTPS autenticado. Nenhum formulário tem acesso a credenciais.

Site e proxy de API na Cloudflare; backend FastAPI no Render e banco persistente externo. Aprovar fluxo em prévia antes do domínio comercial. Banco gratuito temporário e suspensão por ociosidade devem ficar documentados.

## Aceitação

pytest cobre CRUD/contrato, 400/401/403/404/409/422, JWT/expiração/RBAC, filtros, 1:N, migração, rollback atômico e retentativa sem duplicação. CI instala Python 3.12 e roda testes/checagem de contrato sem credenciais. Documentação publicada deve representar a v2, com schemas, exemplos, segurança e Mock preservados.
