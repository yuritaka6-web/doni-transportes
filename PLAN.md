# Plano — migração Python e implantação

Plano escrito antes da implementação desta migração, autorizada pelo autor em 20/11/2026. Execução por etapas; evidências em `docs/VERIFICACAO-PARTE2.md`.

- [x] Registrar constituição, governança, especificação e sequência de migração.
- [x] Extrair Pydantic v2 do domínio existente e definir auth/JWT/erros RFC 9457.
- [x] Criar modelos SQLAlchemy 2.0 tipados, relação 1:N, sessões, inicialização e migração do legado.
- [x] Implementar segurança JWT HS256 e RBAC ADMIN/MEMBER, validação e erros.
- [x] Implementar routers CRUD, paginação/filtros, relação com selectinload e orçamento público atômico.
- [x] Implementar outbox, envio SMTP/HTTPS, retentativas e template com contato WhatsApp.
- [x] Adaptar painel/formulário, exportar contrato v2 e documentação.
- [x] Executar pytest com banco isolado, testar migração/persistência/rollback e transporte.
- [x] Configurar CI Python, implantação Render gratuita e proxy Cloudflare.
- [x] Migrar dados, configurar segredos em canais privados e testar prévia real.
- [x] Publicar código, contrato Apidog e domínio; verificar orçamento e e-mail em produção.

O trabalho permanece individual. Nenhum integrante fictício será acrescentado.
