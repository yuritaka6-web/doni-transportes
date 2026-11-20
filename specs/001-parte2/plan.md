# Plano técnico

1. Registrar requisitos e critérios antes de alterar a implementação.
2. Manter Node.js 24 e SQLite e adicionar Drizzle com adaptador node:sqlite; versão exata no lockfile. A integração nativa está na versão release candidate do ORM: documentar e testar essa escolha.
3. Mapear as tabelas existentes (id, clienteId e dados JSON) no ORM, preservando o formato da Parte 1. O JSON é um campo mapeado; não apresentar esse modelo híbrido como totalmente normalizado. Usuários e sessões usam colunas próprias e referências.
4. Extrair repositório e migrações versionadas. SQL direto fica restrito a migrações, inicialização e testes de diagnóstico.
5. Implementar sessões opacas: token aleatório de 256 bits em cookie HttpOnly; SHA-256 no banco; expiração em 8 horas; scrypt assíncrono para senhas. ADMIN e LEITOR com autorização no servidor. Origem diferente é rejeitada nas mutações autenticadas.
6. Manter POSTs públicos para o formulário; exigir sessão para consultas/alterações/exclusões. Login e formulário com limites de uso em memória por IP, adequados ao processo local; produção exigirá armazenamento compartilhado.
7. Criar painel comercial e contrato v1.1 separado, mantendo intacta a entrega publicada da Parte 1.
8. Executar validação do contrato e testes de integração, revisar diff/segredos e preparar repositório/apresentação.

Referência da integração: https://orm.drizzle.team/docs/sqlite/connect-node-sqlite
