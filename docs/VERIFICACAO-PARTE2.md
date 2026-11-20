# Evidências de validação

Migração Python em 20/11/2026. Governança e especificação precederam o código desta migração; backend anterior e suas evidências permanecem no histórico.

- pytest: 27 testes passaram, sem falhas, usando banco SQLite isolado por cenário.
- Contrato v2: 14 operações, 22 schemas, corpos/respostas referenciados, exemplos validados e exportação comparada ao runtime.
- JWT: assinatura, emissor/audiência, expiração, ausência/invalidade, RBAC ADMIN/MEMBER e senhas scrypt.
- ORM: SQLAlchemy 2.0, colunas tipadas, ForeignKey/relationship 1:N, selectinload com contagem de queries, paginação, persistência após reiniciar e rollback de pedido/contato/outbox.
- Migração real local: preservados 1 cliente, 1 solicitação e 1 operador; origem não alterada. Teste automatizado prova idempotência e login com hash legado.
- Notificação: testes simulados validam contatos/WhatsApp, falha/reenvio e ausência de reenvio por PATCH. Provedor HTTPS aceitou teste autorizado após ativação do destinatário. Não equivale à confirmação de leitura na caixa de entrada.
- Credenciais, banco e bootstrap são privados e excluídos do Git.

Implantação validada na nuvem com API Python no Render, PostgreSQL e proxy/website Cloudflare. O link Quick Share existente preserva a mesma URL e mostra a v2, README e autenticação Bearer.

- CI Python aprovado: https://github.com/yuritaka6-web/doni-transportes/actions/runs/44815019328 (primeira revisão Python).
- As 14 operações do Cloud Mock retornaram os status esperados e respostas válidas contra os schemas v2.
- Resend aceitou a notificação real de validação; remetente do provedor e destinatário verificado do autor. Envio a partir do Render confirmado pela outbox e pelo status Delivered no painel Resend.

## Produção

- CI da revisão com Resend: https://github.com/yuritaka6-web/doni-transportes/actions/runs/44817651526 (pytest + teste do proxy).
- /health retornou 200 e versão 2.0.0 em donitransportes.com.br e www.donitransportes.com.br.
- Verificações remotas no domínio: JWT ausente/credenciais inválidas 401, operador autenticado 200, cadastro 201/Location, leitura/alteração 200, DELETE 204 vazio, busca posterior 404, query inválida 400 e corpo inválido 422.
- Teste pelo navegador no formulário comercial: protocolo 35941f7c-b681-4818-9c90-d004cbd50ceb, outbox ENVIADO em uma tentativa e recibo Delivered no Resend. Dados fictícios identificados como teste; não representam frete real.
- Migração para PostgreSQL preservou o cliente e orçamento locais e o hash da conta do autor. O hash foi comparado sem exibir seu valor; nenhuma senha precisou ser alterada.
- Bootstrap de usuário retirado das variáveis do Render após importação. Chave Resend possui apenas Sending access e não foi publicada.
- 27 testes pytest e 1 teste do proxy passaram. Auditoria de dependências Python não reportou vulnerabilidades conhecidas na revisão verificada.

O plano gratuito permanece sujeito à ociosidade e ao vencimento do PostgreSQL em 20/12/2026. A confirmação Delivered informa aceitação pelo servidor de destino, sem comprovar leitura humana ou localização na caixa principal. O trabalho permanece de autoria individual.
