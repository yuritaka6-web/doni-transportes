# Desenvolvimento assistido por IA e SDD

## Processo aplicado na Parte 2

1. O autor forneceu a rubrica: arquivos de especificação, autenticação, ORM, testes e extras.
2. Antes de alterar o código desta etapa, foram escritos `specs/001-parte2/spec.md`, `plan.md` e `tasks.md` com requisitos identificados e aceitação observável.
3. As decisões conduziram a implementação: preservar o banco, Drizzle para acesso a dados, sessões opacas com papéis e um painel para demonstração.
4. Os testes foram ligados aos critérios AUTH-01/05, ORM-01/02, API-01/02 e TEST-01. A suíte anterior de CRUD e e-mail foi adaptada para autenticar suas consultas.
5. O contrato v1.1 foi validado, os testes executados e as limitações registradas antes da entrega.

## Rastreabilidade

| Critério | Código | Evidência |
| --- | --- | --- |
| AUTH-01/04 | src/auth.mjs; server.mjs | tests/auth.test.mjs: hash, cookie e login |
| AUTH-02 | autorização no servidor | teste de leitura LEITOR e rejeição de PATCH/DELETE |
| AUTH-03 | sessões persistentes e logout | testes de revogação, expiração e Secure |
| AUTH-05 | createLimiter | sexta falha retorna 429 |
| ORM-01/02 | src/db/; migrations/ | teste de banco legado, reinício e rollback |
| API-01/02 | docs/openapi-v1.1.json | check:contract; testes de formulário público e CRUD |
| EXTRA-01 | admin.html; admin.js | demonstração de login, consulta e atualização de status |
| TEST-01 | tests/; workflow CI | npm test; npm run check:contract |

## Exemplos de orientações ao assistente

Resumo fiel das solicitações do autor, sem transcrição de credenciais:

- Usar o site Doni Transportes como base de um projeto acadêmico.
- Substituir o encaminhamento manual por WhatsApp por notificação automática por e-mail, com link para o WhatsApp do cliente.
- Conferir a documentação publicada contra os requisitos antes do envio.
- Acrescentar os critérios da Parte 2: SDD, autenticação, ORM, testes e extras.

## Limites da evidência

O backend inicial já existia quando o Cloud Mock da Parte 1 foi validado. Os documentos desta pasta não devem ser apresentados como prova retroativa de Design-First. A sequência especificação → implementação → validação aqui descrita é da evolução da Parte 2. Testes automatizados não substituem revisão humana nem comprovam entrega de cada e-mail na caixa de entrada.
