# Decisões

- Python 3.12/FastAPI/Pydantic v2/SQLAlchemy 2.0/PyJWT/pytest, conforme migração autorizada. Backend anterior preservado no Git.
- Colunas relacionais tipadas, Cliente 1:N Solicitação, ForeignKey/relationship, selectinload e transações. Solicitação/outbox atômicos.
- SQLite local e PostgreSQL persistente em produção. Inicialização aditiva versionada e importador idempotente preservam o legado.
- JWT HS256 de uma hora, emissor/audiência verificados, papéis ADMIN/MEMBER, senhas scrypt e ausência de senha padrão. Contatos privados; formulário anônimo em endpoint próprio com limite de uso.
- Erros RFC 9457; nenhuma resposta expõe exceções de banco/SMTP ou segredos.
- API HTTPS Resend para contornar bloqueio SMTP gratuito, com chave somente de envio, outbox, retentativas e idempotência de 24 horas. FormSubmit foi testado e rejeitado para produção após bloqueios 403/429 vindos da nuvem. SMTP TLS disponível em ambiente compatível.
- Cloudflare serve assets/proxy; regras de negócio e banco executam em Python.
- Suspensão por ociosidade e expiração do banco em 30 dias são limites explícitos do plano gratuito; sem contratação automática de recursos pagos.
