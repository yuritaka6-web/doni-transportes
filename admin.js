const $=id=>document.getElementById(id);
let operator,page=1,loading=false;
function feedback(message,error=false){$('feedback').textContent=message;$('feedback').className=`status ${error?'error':'success'}`;}
function showLogin(){operator=null;$('login-panel').hidden=false;$('dashboard').hidden=true;$('orders').replaceChildren();}
async function api(path,method='GET',body){
  const response=await fetch('/api/v1/'+path,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,credentials:'same-origin'});
  const data=response.status===204?null:await response.json();
  if(!response.ok){if(response.status===401)showLogin();throw new Error(data?.mensagem||'Não foi possível concluir a operação.');}
  return data;
}
function text(tag,value){const el=document.createElement(tag);el.textContent=value;return el;}
async function loadOrders(){
  if(loading)return;loading=true;$('refresh').disabled=true;
  try {
    const status=$('status-filter').value;
    const data=await api(`solicitacoes-orcamento?pagina=${page}&limite=10${status?'&status='+encodeURIComponent(status):''}`);
    const contacts=new Map();
    await Promise.all([...new Set(data.dados.map(p=>p.clienteId))].map(async id=>contacts.set(id,await api('clientes/'+id))));
    const rows=[];
    for(const order of data.dados){
      const client=contacts.get(order.clienteId),row=document.createElement('tr');
      const first=text('td',client.nome);first.append(text('small',order.id),text('small',`Coleta: ${order.dataColeta}`));
      const route=text('td',`${order.origem.cidade}/${order.origem.uf} → ${order.destino.cidade}/${order.destino.uf}`);route.append(text('small',`${order.pesoKg} kg · ${order.descricaoCarga}`));if(order.observacoes)route.append(text('small',order.observacoes));
      const contact=document.createElement('td');
      const email=text('a',client.email);email.href='mailto:'+client.email;
      const whatsapp=text('a','Conversar no WhatsApp');whatsapp.href='https://wa.me/'+client.telefone.replace(/\D/g,'');whatsapp.target='_blank';whatsapp.rel='noopener noreferrer';
      contact.append(email,document.createElement('br'),whatsapp,text('small',`E-mail da solicitação: ${order.statusEmail}`));
      const action=document.createElement('td');const select=document.createElement('select');select.setAttribute('aria-label',`Status do pedido ${order.id}`);
      for(const value of ['RECEBIDA','EM_ANALISE','COTADA','CANCELADA']){const option=text('option',value);option.value=value;select.append(option);}select.value=order.status;select.disabled=operator.papel!=='ADMIN';action.append(select);
      if(operator.papel==='ADMIN'){
        const button=text('button','Salvar status');button.type='button';button.addEventListener('click',async()=>{button.disabled=true;try{await api('solicitacoes-orcamento/'+order.id,'PATCH',{status:select.value});feedback('Status atualizado.');}catch(error){feedback(error.message,true);}finally{button.disabled=false;}});action.append(button);
      }
      row.append(first,route,contact,action);rows.push(row);
    }
    if(!rows.length){const row=document.createElement('tr'),cell=text('td','Nenhuma solicitação encontrada.');cell.colSpan=4;cell.className='empty';row.append(cell);rows.push(row);}
    $('orders').replaceChildren(...rows);$('pagination').textContent=`Página ${page} · ${data.paginacao.total} ${data.paginacao.total===1?'pedido':'pedidos'}`;$('previous').disabled=page===1;$('next').disabled=page>=data.paginacao.totalPaginas;
  }catch(error){feedback(error.message,true);}finally{loading=false;$('refresh').disabled=false;}
}
async function enter(user){operator=user;$('operator').textContent=`${user.nome} · ${user.papel}`;$('login-panel').hidden=true;$('dashboard').hidden=false;page=1;await loadOrders();}
$('login-form').addEventListener('submit',async event=>{event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;try{const data=await api('auth/login','POST',{email:$('operator-email').value,senha:$('operator-password').value});$('operator-password').value='';feedback('');await enter(data.usuario);}catch(error){feedback(error.message,true);}finally{button.disabled=false;}});
$('logout').addEventListener('click',async()=>{try{await api('auth/logout','POST');showLogin();feedback('Sessão encerrada.');}catch(error){feedback(error.message,true);}});
$('status-filter').addEventListener('change',()=>{page=1;void loadOrders();});$('refresh').addEventListener('click',()=>void loadOrders());$('previous').addEventListener('click',()=>{if(page>1){page--;void loadOrders();}});$('next').addEventListener('click',()=>{page++;void loadOrders();});
api('auth/me').then(data=>enter(data.usuario)).catch(()=>showLogin());
