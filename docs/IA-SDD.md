# Desenvolvimento com IA e SDD

Autor e revisor humano: Yuri Vinicius Decaris Trevelin. Ferramenta: Codex. O assistente propôs especificações, código e testes conforme orientações do autor.

O backend inicial em Node precedeu a validação do Cloud Mock. Não há prova retroativa de Design-First. A primeira evolução da Parte 2 foi especificada em specs/001-parte2 antes da implementação. Essa pasta e os contratos v1/v1.1 são referências históricas.

Em 20/11/2026 o autor autorizou migrar para Python/FastAPI, Pydantic v2, SQLAlchemy 2.0, JWT e pytest, após comparar as aulas 10/11. STYLEGUIDE, AGENTS, SPEC e PLAN foram escritos antes do código da migração. O commit de governança antecede o de implementação. As personas descrevem etapas do mesmo assistente; não representam integrantes ou revisores adicionais.

Rastreabilidade: STYLEGUIDE/AGENTS → SPEC → PLAN → src/api → pytest/CI e OpenAPI exportado. A revisão preservou o domínio e substituiu JSON de domínio por colunas tipadas. O formulário possui endpoint público atômico; o CRUD administrativo requer JWT.

Evidências em src/api/tests e VERIFICACAO-PARTE2.md. Distinguir testes de transporte simulado, aceitação pelo provedor e entrega/leitura pelo destinatário.
