# Roteiro de apresentação — Parte 2

## Preparar antes da aula

1. Instalar Node.js 24 e executar `npm ci`.
2. Copiar `.env.example` para `.env` somente se ainda não houver configuração. Não mostrar esse arquivo na projeção: contém a senha SMTP.
3. Executar `npm run admin:create -- seu-email` e escolher nome/senha. Não há credencial padrão no repositório.
4. Executar `npm start`; abrir `http://127.0.0.1:3000` e `http://127.0.0.1:3000/admin.html`.
5. Separar o link do repositório e o link público do Apidog. Preparar o terminal para `npm run check:contract` e `npm test`.

## Demonstração sugerida — 7 a 10 minutos

| Tempo | Ação | O que explicar |
| --- | --- | --- |
| 1 min | Apresentar problema e autoria | Site para captar pedidos de frete; contato e atendimento comercial |
| 1 min | Abrir specs/001-parte2 | Requisitos, plano e critérios antes da implementação desta evolução |
| 1 min | Mostrar docs/openapi-v1.1.json e Apidog v1 | Contratos reutilizáveis; distinguir mock de backend real |
| 1 min | Abrir /api/v1/clientes sem login | 401: informações protegidas |
| 2 min | Preencher orçamento pelo site e entrar no painel | POSTs públicos; consultas privadas; pedido salvo; contato do cliente disponível ao operador |
| 1 min | Atualizar status e sair | PATCH autorizado; logout revoga sessão |
| 1 min | Mostrar src/db/schema.mjs e migrações | ORM real, chaves estrangeiras, modelo híbrido e preservação dos dados |
| 1 min | Executar contrato e testes | CRUD, autorização, sessão, migração, rollback e SMTP simulado |

## Pontos que o autor precisa saber explicar

- Diferença entre autenticação (quem entrou) e autorização (o que cada papel pode fazer).
- Por que a senha não fica em texto puro e por que o token da sessão também é hasheado.
- Por que o cookie é HttpOnly e SameSite=Strict; Secure em HTTPS.
- Como a transação evita um pedido sem notificação enfileirada.
- Como o Drizzle mapeia tabelas e parametriza consultas; por que a migração é aditiva.
- Por que o mock não persiste o CRUD nem testa entrega real de e-mails.
- Onde a IA ajudou e quais limitações permanecem.

## Extras demonstráveis

Painel comercial com filtros/paginação, papéis ADMIN/LEITOR, outbox SMTP com reenvio, link WhatsApp do cliente, validação derivada do OpenAPI e workflow de CI no GitHub.

Não use dados de clientes reais na apresentação. Para demonstrar e-mail, use um contato de teste autorizado e explique que ENVIADO confirma o aceite SMTP. Não projete senha, cookie de sessão nem `.env`.
