import nodemailer from 'nodemailer';

const escape = value => String(value ?? 'Não informado').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

export function buildMessage(cliente, pedido, config) {
  const whatsapp = `https://wa.me/${cliente.telefone.replace(/\D/g, '')}?text=${encodeURIComponent(`Olá, ${cliente.nome}! Recebemos sua solicitação de orçamento ${pedido.id} na Doni Transportes.`)}`;
  const rows = [
    ['Protocolo', pedido.id], ['Cliente', cliente.nome], ['Tipo de pessoa', cliente.tipoPessoa],
    ['E-mail', cliente.email], ['WhatsApp', cliente.telefone],
    ['Origem', `${pedido.origem.cidade} / ${pedido.origem.uf}`],
    ['Destino', `${pedido.destino.cidade} / ${pedido.destino.uf}`],
    ['Carga', pedido.descricaoCarga], ['Peso estimado', `${pedido.pesoKg} kg`],
    ['Coleta desejada', pedido.dataColeta], ['Observações', pedido.observacoes],
  ];
  return {
    from: { name: 'Doni Transportes — Site', address: config.from },
    to: config.to,
    replyTo: { name: cliente.nome, address: cliente.email },
    messageId: `<orcamento-${pedido.id}@doni-transportes.local>`,
    subject: `Nova solicitação de orçamento — ${pedido.id}`,
    text: `DONI TRANSPORTES\nNova solicitação de orçamento\n\n${rows.map(([k,v]) => `${k}: ${v ?? 'Não informado'}`).join('\n')}\n\nConversar com o cliente no WhatsApp: ${whatsapp}\n\nOs dados acima foram informados pelo cliente.`,
    html: `<div style="font-family:Arial,sans-serif;color:#202020;max-width:680px;margin:auto"><div style="background:#0f0f0f;color:#00ff66;padding:24px"><h1 style="margin:0">Doni Transportes</h1><p style="color:white">Nova solicitação de orçamento</p></div><table style="border-collapse:collapse;width:100%">${rows.map(([k,v]) => `<tr><th style="text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #ddd">${escape(k)}</th><td style="padding:12px;border-bottom:1px solid #ddd;white-space:pre-wrap;overflow-wrap:anywhere">${escape(v)}</td></tr>`).join('')}</table><p style="margin:28px 0"><a href="${escape(whatsapp)}" style="background:#00a642;color:white;padding:14px 20px;border-radius:6px;text-decoration:none">Conversar com o cliente no WhatsApp</a></p><p>Responder a este e-mail direciona a resposta ao cliente.</p><p style="color:#666">Dados informados pelo cliente; confirme a disponibilidade antes de fechar o frete.</p></div>`,
    disableFileAccess: true,
    disableUrlAccess: true,
  };
}

export function mailConfig(env = process.env) {
  const config = { to: env.COMPANY_EMAIL || 'yuri.taka6@gmail.com', from: env.MAIL_FROM || env.SMTP_USER,
    host: env.SMTP_HOST, port: Number(env.SMTP_PORT || 465), secure: env.SMTP_SECURE !== 'false',
    user: env.SMTP_USER, pass: env.SMTP_PASS };
  config.ready = Boolean(config.to && config.from && config.host && config.user && config.pass);
  return config;
}

export function createMailer(repo, config = mailConfig(), transport) {
  const smtp = transport || (config.ready ? nodemailer.createTransport({
    host: config.host, port: config.port, secure: config.secure,
    requireTLS: !config.secure,
    auth: { user: config.user, pass: config.pass },
    connectionTimeout: 10000, greetingTimeout: 10000, socketTimeout: 15000,
  }) : null);
  let running = false;
  let timer;
  async function flush() {
    if (!smtp) return;
    if (running) {
      while (running) await new Promise(resolve => setTimeout(resolve, 10));
      return;
    }
    running = true;
    try {
      const pending = repo.pending();
      for (const row of pending) {
        try {
          const snapshot = row.payload;
          const result = await smtp.sendMail(buildMessage(snapshot.cliente, snapshot.pedido, config));
          if (!result.accepted?.length) throw new Error('SMTP_REJEITOU');
          repo.markSent(row.solicitacaoId);
        } catch (error) {
          // Não registra senhas, conteúdo de e-mail nem resposta SMTP com dados pessoais.
          const code = typeof error.code === 'string' ? error.code : 'ENVIO_FALHOU';
          const delay = Math.min(3600000, 30000 * 2 ** Math.min(row.tentativas, 7));
          repo.markFailed(row.solicitacaoId,code,Date.now()+delay);
          console.error(`Notificação ${row.solicitacaoId}: ${code}; reenvio agendado.`);
        }
      }
    } finally { running = false; }
  }
  return {
    flush,
    start() { if (smtp) { timer = setInterval(() => void flush(), 30000); timer.unref(); void flush(); } },
    async stop() { clearInterval(timer); while (running) await new Promise(resolve => setTimeout(resolve, 20)); smtp?.close?.(); },
    enqueue(cliente, pedido) {
      repo.enqueue(cliente,pedido);
    },
  };
}
