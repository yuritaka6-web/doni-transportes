# Implantação

A API executa em Python/FastAPI no Render; o site/proxy permanece na Cloudflare. Node/Wrangler é ferramenta de implantação, sem regras de domínio.

## Render

Python 3.12.10; build: pip install -r src/api/requirements.txt; start: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT; health: /health. Serviço e banco na mesma região. DATABASE_URL recebe a conexão interna PostgreSQL; psycopg é o driver. Nunca usar SQLite em disco efêmero de produção.

Variáveis: ENVIRONMENT=production, JWT_SECRET aleatório com 32+ caracteres, MAIL_TRANSPORT=formsubmit, COMPANY_EMAIL e PUBLIC_ORIGIN. PROXY_SECRET coincide com o secret do Worker para confiar no IP encaminhado. BOOTSTRAP_USERS_JSON opcional contém hashes scrypt e deve ser tratado como segredo, removido após importar. Não há senha padrão de produção.

render.yaml descreve uma instalação nova. Não aplicar outro Blueprint sobre recursos existentes sem revisar nomes/IDs. O banco gratuito criado em 20/11/2026 expira em 20/12/2026; exporte/migre antes dessa data. A API suspende por ociosidade; a fila retoma quando o processo acorda. O plano gratuito serve à validação acadêmica; atendimento comercial contínuo requer banco sem expiração e serviço sem suspensão.

## Cloudflare

npm ci; npm run build; npx wrangler deploy. O build copia apenas assets públicos para dist. API_ORIGIN fica em wrangler.jsonc; PROXY_SECRET é secret. Não publicar a raiz como assets, pois contém código e pode conter arquivos locais privados. Preservar os domínios personalizados do Worker existente. Testar /health e orçamento em prévia antes de trocar a produção.

## E-mail

O destinatário FormSubmit é ativado por e-mail. O backend envia HTTPS com contatos, Reply-To e link wa.me. Dados são processados pelo fornecedor; submissões são retidas por 30 dias segundo https://formsubmit.co/documentation. A outbox mantém tentativas sem repetir cadastro; envio aceito não garante leitura. A conexão externa ao banco deve ser limitada/revogável e credenciais nunca publicadas.

Se o repositório voltar a ser privado, a implantação continua ativa, mas novos builds por URL pública exigirão um provedor Git autorizado ou acesso ao código novamente.
