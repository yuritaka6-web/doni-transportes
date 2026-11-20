# Evidências de validação — Parte 2

Verificação local em 20/11/2026, com Node.js 24.14.0.

| Verificação | Resultado observado |
| --- | --- |
| Instalação limpa com npm ci no checkout do repositório | Concluída |
| npm run check:contract | OpenAPI válido; 13 operações; 23 schemas; corpos/respostas por referência e exemplos válidos |
| npm test | 12 testes passaram, sem falhas |
| npm audit --omit=dev --audit-level=high | Nenhuma vulnerabilidade reportada |
| Migração de banco legado | Dados preservados após aplicar migrações e reabrir |
| Transação ORM | Falha simulada provocou rollback do pedido |
| Credenciais no repositório | .env, banco e node_modules excluídos |

Os testes de e-mail desta etapa usam transporte simulado. A Parte 1 teve teste real aceito pelo SMTP do Gmail, sem garantia de entrega na caixa de entrada. O Cloud Mock e o link do Apidog preservam a versão inicial. A execução de CI remota deve ser conferida na aba Actions após o push; os resultados acima não são uma declaração sobre o GitHub Actions.
