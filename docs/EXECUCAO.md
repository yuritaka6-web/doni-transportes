> Guia histórico da Parte 1. Para executar a Parte 2 com autenticação, use o README da raiz. O contrato atual é openapi-v1.1.json.

# Operação e verificação local

O comando `npm start` serve o site e a API na mesma origem, em `http://127.0.0.1:3000`. Requer Node.js 24+. O SQLite integrado ao Node pode emitir aviso de recurso experimental nessa versão; isso não indica falha da aplicação.

## Configuração

| Variável | Uso |
| --- | --- |
| PORT | Porta HTTP; padrão 3000 |
| DB_PATH | Caminho do SQLite; padrão data/doni.sqlite |
| COMPANY_EMAIL | Destinatário fixo das notificações; configurado como yuri.taka6@gmail.com |
| SMTP_HOST / SMTP_PORT | Servidor de envio e porta |
| SMTP_SECURE | true para TLS direto, usualmente porta 465; false para STARTTLS obrigatório |
| SMTP_USER / SMTP_PASS | Conta e senha de app do remetente |
| MAIL_FROM | E-mail remetente autorizado no SMTP |

O processo lê `.env` ao iniciar. Não existe senha embutida no código ou no navegador. A configuração é do servidor. O destinatário nunca é aceito do cliente da API.

## Persistência e fila

O SQLite contém clientes, solicitações e a outbox técnica. A criação de pedido e notificação usa uma única transação. O processamento é assíncrono e a API retorna 201 com statusEmail=PENDENTE. Consulte novamente o pedido para observar ENVIADO ou FALHOU.

A notificação captura os dados na criação; alterar o cadastro posteriormente não muda o e-mail já preparado. Excluir o pedido exclui a notificação da fila; e-mails que já tenham sido enviados ou estejam em transmissão não podem ser recolhidos. O remetente e o destinatário são aplicados conforme a configuração atual na hora do envio.

Sem SMTP configurado, a fila não é drenada. Depois de configurar e reiniciar, os pendentes são reenviados. O conteúdo inclui dados pessoais: trate o arquivo de banco como privado e mantenha backups antes de qualquer alteração manual.

## Comandos de validação

```powershell
npm run check:contract
npm test
npm audit --omit=dev --audit-level=high
```

O verificador valida o OpenAPI, a contagem de operações, referências e exemplos. A suíte cobre CRUD das duas entidades, paginação, filtros, validação de campos, proteção de arquivos locais, integridade de relacionamento, banco após reinício, template de e-mail, reenvio, SMTP simulado e mock local.

Os testes não usam o Gmail real. O aceite SMTP simulado não demonstra chegada de e-mail real, classificação de spam ou autorização da conta remetente.

## Limites para implantação

O backend está restrito a loopback e não tem login. Esta versão atende desenvolvimento e demonstração acadêmica. Para produção, implemente autenticação e autorização para operações administrativas, proteção contra abuso do formulário, HTTPS e política de dados pessoais. Use hospedagem que execute Node e mantenha o banco em armazenamento persistente; cópias efêmeras do SQLite podem perder dados após reinício da hospedagem. O domínio público e o repositório remoto não foram alterados nesta implementação.
