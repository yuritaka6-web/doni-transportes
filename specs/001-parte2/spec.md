# Especificação — Parte 2: API administrável

Status: especificação da evolução, escrita antes da implementação desta etapa.
Base existente: site, contrato REST v1, CRUD de clientes/solicitações, validação Ajv e outbox de e-mail.

## Requisitos e aceitação

| ID | Requisito | Aceitação verificável |
| --- | --- | --- |
| AUTH-01 | Autenticar operador com e-mail e senha | Login correto cria sessão; incorreto retorna 401 sem revelar existência da conta |
| AUTH-02 | Proteger contatos e operações administrativas | GET de domínio sem sessão retorna 401; ADMIN lê e modifica; LEITOR lê mas recebe 403 ao modificar |
| AUTH-03 | Encerrar e expirar sessões | Logout revoga token; sessão expirada não autoriza; cookie HttpOnly e SameSite=Strict |
| AUTH-04 | Guardar credenciais com segurança | Senha derivada com scrypt e salt aleatório; somente hash do token fica no banco; sem conta/senha padrão |
| AUTH-05 | Conter tentativas de login | Limite de cinco falhas em 15 minutos por IP; 429 na próxima tentativa; mensagens genéricas |
| ORM-01 | Usar ORM no acesso às entidades e fila | Schema Drizzle, consultas parametrizadas e transação pedido/outbox; sem montagem de SQL com dados do usuário |
| ORM-02 | Preservar o banco da Parte 1 | Migrações aditivas e versionadas; clientes/pedidos existentes permanecem acessíveis |
| API-01 | Preservar formulário público | POST cliente e POST solicitação continuam públicos; criação de contato não expõe listas ou dados de terceiros |
| API-02 | Evoluir o contrato | Contrato v1.1 separado do v1 publicado; schemas de login/usuário e respostas 401/403/429; autenticação por cookie |
| EXTRA-01 | Painel comercial | Operador entra, lista solicitações, altera status e sai; erros e sessão expirada têm tratamento visível |
| TEST-01 | Testes repetíveis | CRUD, validação, autenticação, autorização, expiração, revogação, persistência, migrações e e-mail simulado passam sem segredos |
| SDD-01 | Rastrear especificação até evidências | spec.md → plan.md → tasks.md → código/testes; registro honesto de uso de IA e decisões |

## Regras de negócio

Uma solicitação pertence a um cliente. Clientes com solicitações não podem ser excluídos. A criação de solicitação e notificação é atômica. O e-mail usa uma cópia dos dados no momento da criação e não é reenviado por PATCH. SMTP é configurado apenas no servidor. O formulário registra a solicitação antes de confirmar sucesso ao visitante.

## Fora do escopo

Cadastro público de operadores, recuperação de senha por e-mail, pagamentos, GPS e implantação pública. A conta inicial é criada por comando local com senha escolhida pelo responsável.

## Honestidade do processo

Esta especificação orienta a Parte 2 a partir do estado já existente. Não representa evidência retroativa de que o backend da Parte 1 foi implementado depois do Cloud Mock.
