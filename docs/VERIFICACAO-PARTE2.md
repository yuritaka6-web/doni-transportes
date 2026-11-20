# Evidências de validação

Migração Python em 20/11/2026. Governança e especificação precederam o código desta migração; backend anterior e suas evidências permanecem no histórico.

- pytest: 27 testes passaram, sem falhas, usando banco SQLite isolado por cenário.
- Contrato v2: 14 operações, 22 schemas, corpos/respostas referenciados, exemplos validados e exportação comparada ao runtime.
- JWT: assinatura, emissor/audiência, expiração, ausência/invalidade, RBAC ADMIN/MEMBER e senhas scrypt.
- ORM: SQLAlchemy 2.0, colunas tipadas, ForeignKey/relationship 1:N, selectinload com contagem de queries, paginação, persistência após reiniciar e rollback de pedido/contato/outbox.
- Migração real local: preservados 1 cliente, 1 solicitação e 1 operador; origem não alterada. Teste automatizado prova idempotência e login com hash legado.
- Notificação: testes simulados validam contatos/WhatsApp, falha/reenvio e ausência de reenvio por PATCH. Provedor HTTPS aceitou teste autorizado após ativação do destinatário. Não equivale à confirmação de leitura na caixa de entrada.
- Credenciais, banco e bootstrap são privados e excluídos do Git.

Implantação Render/Cloudflare, CI remoto e atualização Apidog serão registrados abaixo após validação real. Esta seção não declara esses passos concluídos antecipadamente.

- CI Python aprovado: https://github.com/yuritaka6-web/doni-transportes/actions/runs/44815019328 (primeira revisão Python).
- As 14 operações do Cloud Mock retornaram os status esperados e respostas válidas contra os schemas v2.
- Resend aceitou a notificação real de validação; remetente do provedor e destinatário verificado do autor. Validação do envio a partir do Render ainda pendente nesta revisão.
