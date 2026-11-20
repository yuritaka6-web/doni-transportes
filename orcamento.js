for (const form of document.querySelectorAll('.quote-form')) {
  let savedCliente;
  let savedFingerprint;
  const result = form.querySelector('[role=status]');
  const submit = form.querySelector('button[type=submit]');
  const report = (message, type) => { result.textContent = message; result.className = `form-result ${type}`; };
  async function post(path, payload) {
    const response = await fetch(`/api/v1/${path}`, {
      method:'POST', headers:{ 'Content-Type':'application/json' }, body:JSON.stringify(payload),
    });
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) throw new Error('O serviço de orçamento está indisponível. Tente novamente mais tarde.');
    const body = await response.json();
    if (!response.ok) {
      const fields = body.detalhes?.map(item=>item.campo).join(', ');
      throw new Error(`${body.mensagem || 'Não foi possível registrar o pedido.'}${fields ? ` Verifique: ${fields}.` : ''}`);
    }
    return body;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = Object.fromEntries(new FormData(form));
    let digits = data.telefone.replace(/\D/g,'');
    if (digits.length === 10 || digits.length === 11) digits = `55${digits}`;
    if (!/^55[1-9][0-9][0-9]{8,9}$/.test(digits)) {
      report('Informe um WhatsApp brasileiro com DDD, por exemplo: (16) 99123-4567.','error'); return;
    }
    const cliente = { nome:data.nome.trim(),email:data.email.trim(),telefone:`+${digits}`,tipoPessoa:data.tipoPessoa };
    if (cliente.nome.length < 2 || data.descricaoCarga.trim().length < 10 || data.origemCidade.trim().length < 2 || data.destinoCidade.trim().length < 2) {
      report('Preencha seu nome e as cidades de origem e destino. Descreva a carga com pelo menos 10 caracteres.','error'); return;
    }
    submit.disabled = true; submit.textContent = 'Registrando solicitação…';
    result.textContent = '';
    try {
      const fingerprint = JSON.stringify(cliente);
      if (!savedCliente || fingerprint !== savedFingerprint) {
        savedCliente = await post('clientes',cliente);
        savedFingerprint = fingerprint;
      }
      const pedido = await post('solicitacoes-orcamento',{
        clienteId:savedCliente.id,
        origem:{ cidade:data.origemCidade.trim(),uf:data.origemUf },
        destino:{ cidade:data.destinoCidade.trim(),uf:data.destinoUf },
        descricaoCarga:data.descricaoCarga.trim(),pesoKg:Number(data.pesoKg),dataColeta:data.dataColeta,
        observacoes:data.observacoes.trim() || null,
      });
      report(`Solicitação registrada! Protocolo: ${pedido.id}. Seus dados foram encaminhados para atendimento. A equipe poderá entrar em contato por e-mail ou WhatsApp.`, 'success');
      form.querySelectorAll('input,select,textarea').forEach(input=>input.disabled=true);
      submit.textContent = 'Solicitação registrada';
      result.focus();
    } catch (error) {
      report(error instanceof TypeError ? 'Não foi possível conectar ao serviço de orçamento. Confira sua conexão e tente novamente.' : error.message,'error');
      submit.disabled = false; submit.textContent = 'Solicitar orçamento';
    }
  });
}
