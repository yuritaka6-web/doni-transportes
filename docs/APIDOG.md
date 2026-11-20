# Contrato publicado no Apidog

Contrato vigente: openapi-v2.json, exportado de schemas/rotas FastAPI e enriquecido com exemplos e regras de Mock. São 14 operações, 22 schemas e segurança JWT Bearer no CRUD administrativo. Os contratos v1/v1.1 foram mantidos como histórico.

Importar a v2 no projeto existente com mesclagem por método/caminho, preservando o README e a URL Quick Share. Organizar Clientes, Solicitações de orçamento, Autenticação e Formulário público; todos os corpos e respostas devem continuar por referência. Excluir a operação histórica auth/logout, pois o cliente JWT encerra a sessão descartando o token. Revisar o README com APIDOG-README.md.

Compartilhamento: incluir README, endpoints e schemas; Try it Out e Cloud Mock habilitados. Nunca incluir senhas/JWT ou segredos de infraestrutura no ambiente compartilhado. O Cloud Mock permite simular operações administrativas sem expor dados do banco comercial. Usar ambiente de produção exige token individual obtido no login.

O histórico Design-First não é reescrito: a primeira implementação precedeu a validação Cloud Mock; esta exportação corresponde à migração Python especificada em SPEC.md e PLAN.md.
