import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { createApp } from '../server.mjs';
import { validators } from '../validation.mjs';
import { createMock } from '../mock-server.mjs';

const sessions=new Map();
async function authenticatedBase(app){
  const base=await app.start(0);
  if(!app.db.prepare('SELECT 1 FROM usuarios WHERE email=?').get('admin@example.com'))await app.auth.createUser({nome:'Operador de teste',email:'admin@example.com',password:'SenhaDeTesteSomente123!'});
  const login=await fetch(base+'/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'admin@example.com',senha:'SenhaDeTesteSomente123!'})});
  sessions.set(base,login.headers.get('set-cookie').split(';')[0]);return base;
}
const cliente = {nome:'Empresa de Teste',email:'cliente@example.com',telefone:'+5516991234567',tipoPessoa:'PJ'};
const pedido = clienteId => ({clienteId,origem:{cidade:'Ribeirão Preto',uf:'SP'},destino:{cidade:'Campinas',uf:'SP'},descricaoCarga:'Caixas de peças automotivas.',pesoKg:350.5,dataColeta:'2026-12-10'});
async function request(base,path,method='GET',body,extra={}) {
  const res = await fetch(base+'/api/v1/'+path,{method,headers:{...(sessions.has(base)?{Cookie:sessions.get(base)}:{}),...(body!==undefined?{'Content-Type':'application/json'}:{}),...extra},body:body===undefined?undefined:JSON.stringify(body)});
  return {res,body:res.status===204?null:await res.json()};
}
function conforms(name,value) { assert.ok(validators[name](value),JSON.stringify(validators[name].errors)); }

test('CRUD completo, filtros, relacionamento, validações e privacidade de arquivos',async t=>{
  const app=createApp({dbPath:':memory:',mailConfig:{ready:false,to:'empresa@example.com'}});
  const base=await authenticatedBase(app);
  t.after(()=>app.stop());
  let r=await request(base,'clientes','POST',cliente);
  assert.equal(r.res.status,201); conforms('Cliente',r.body);
  const c=r.body;
  assert.equal(r.res.headers.get('location'),`/api/v1/clientes/${c.id}`);
  r=await request(base,`clientes/${c.id}`); assert.equal(r.body.nome,cliente.nome);
  r=await request(base,'clientes?busca=Empresa&pagina=1&limite=1'); conforms('ListaClientes',r.body); assert.equal(r.body.dados.length,1);
  r=await request(base,'clientes?busca=inexistente'); assert.equal(r.body.paginacao.total,0); assert.equal(r.body.paginacao.totalPaginas,0);
  r=await request(base,`clientes/${c.id}`,'PATCH',{nome:'Cliente Alterado'}); assert.equal(r.body.nome,'Cliente Alterado'); conforms('Cliente',r.body);
  r=await request(base,'solicitacoes-orcamento','POST',pedido(c.id)); assert.equal(r.res.status,201); conforms('SolicitacaoOrcamento',r.body);
  const p=r.body;
  assert.equal(p.statusEmail,'PENDENTE'); assert.equal(p.observacoes,null);
  assert.equal(app.db.prepare('SELECT COUNT(*) AS n FROM outbox').get().n,1);
  r=await request(base,`solicitacoes-orcamento/${p.id}`); conforms('SolicitacaoOrcamento',r.body);
  r=await request(base,`solicitacoes-orcamento?clienteId=${c.id}&status=RECEBIDA`); conforms('ListaSolicitacoes',r.body); assert.equal(r.body.dados.length,1);
  r=await request(base,`solicitacoes-orcamento/${p.id}`,'PATCH',{status:'EM_ANALISE',observacoes:'Coleta à tarde.'}); assert.equal(r.body.status,'EM_ANALISE');
  r=await request(base,`solicitacoes-orcamento/${p.id}`,'PATCH',{observacoes:null}); assert.equal(r.body.observacoes,null);
  r=await request(base,`clientes/${c.id}`,'DELETE'); assert.equal(r.res.status,409); conforms('ApiError',r.body);
  for (const query of ['pagina=0','limite=101','pagina=1.5','pagina=1&pagina=2','outro=1','busca=']) {
    r=await request(base,'clientes?'+query); assert.equal(r.res.status,400,query); conforms('ApiError',r.body);
  }
  for (const [path,method,body,status] of [
    ['clientes','POST',{...cliente,email:'ruim'},422],['clientes','POST',{...cliente,nome:'  '},422],
    ['clientes','POST',{...cliente,extra:'x'},422],['clientes','POST',null,422],
    [`clientes/${c.id}`,'PATCH',{},422],[`clientes/${c.id}`,'PATCH',{nome:null},422],
    ['solicitacoes-orcamento','POST',pedido(randomUUID()),422],
    ['solicitacoes-orcamento','POST',{...pedido(c.id),pesoKg:-1},422],
    ['solicitacoes-orcamento','POST',{...pedido(c.id),dataColeta:'2026-02-30'},422],
    ['solicitacoes-orcamento','POST',{...pedido(c.id),origem:{cidade:'Xyz',uf:'XX'}},422],
    [`solicitacoes-orcamento/${p.id}`,'PATCH',{clienteId:c.id},422],
    ['clientes/invalido','GET',undefined,400],[`clientes/${randomUUID()}`,'GET',undefined,404],
    [`clientes/${randomUUID()}`,'PATCH',{nome:'Teste'},404],[`clientes/${randomUUID()}`,'DELETE',undefined,404],
    ['clientes','PUT',{},405],
  ]) { r=await request(base,path,method,body); assert.equal(r.res.status,status,`${method} ${path}`); conforms('ApiError',r.body); }
  const invalid=await fetch(base+'/api/v1/clientes',{method:'POST',headers:{'Content-Type':'application/json'},body:'{'}); assert.equal(invalid.status,400);
  const media=await fetch(base+'/api/v1/clientes',{method:'POST',body:'{}'}); assert.equal(media.status,415);
  const large=await fetch(base+'/api/v1/clientes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome:'x'.repeat(66000)})}); assert.equal(large.status,413);
  for (const path of ['/.env','/data/doni.sqlite','/server.mjs']) assert.equal((await fetch(base+path)).status,404);
  assert.equal((await fetch(base+'/orcamento.html')).status,200);
  r=await request(base,`solicitacoes-orcamento/${p.id}`,'DELETE'); assert.equal(r.res.status,204); assert.equal(r.body,null);
  assert.equal(app.db.prepare('SELECT COUNT(*) AS n FROM outbox').get().n,0);
  r=await request(base,`solicitacoes-orcamento/${p.id}`); assert.equal(r.res.status,404);
  r=await request(base,`clientes/${c.id}`,'DELETE'); assert.equal(r.res.status,204); assert.equal(await r.res.text(),'');
});

test('SMTP simulado recebe contatos e WhatsApp do cliente; PATCH não reenvia',async t=>{
  const sent=[];
  const app=createApp({dbPath:':memory:',mailConfig:{ready:true,to:'empresa@example.com',from:'site@example.com'},transport:{sendMail:async msg=>{sent.push(msg);return {accepted:['empresa@example.com']};}}});
  const base=await authenticatedBase(app); t.after(()=>app.stop());
  const c=(await request(base,'clientes','POST',{...cliente,nome:'Cliente <script>alert(1)</script>'})).body;
  const p=(await request(base,'solicitacoes-orcamento','POST',pedido(c.id))).body;
  await app.mailer.flush();
  // flush do setImmediate pode estar em andamento; aguarda apenas a conclusão local.
  for(let i=0;i<100 && sent.length===0;i++) await new Promise(r=>setTimeout(r,5));
  assert.equal(sent.length,1);
  assert.equal(sent[0].to,'empresa@example.com'); assert.equal(sent[0].replyTo.address,cliente.email);
  assert.ok(sent[0].html.includes('https://wa.me/5516991234567'));
  assert.ok(sent[0].html.includes('&lt;script&gt;')); assert.ok(!sent[0].html.includes('<script>'));
  assert.ok(sent[0].text.includes('350.5 kg'));
  await request(base,`solicitacoes-orcamento/${p.id}`,'PATCH',{status:'COTADA'}); await app.mailer.flush();
  assert.equal(sent.length,1);
  const updated=(await request(base,`solicitacoes-orcamento/${p.id}`)).body;
  assert.equal(updated.statusEmail,'ENVIADO'); conforms('SolicitacaoOrcamento',updated);
});

test('falha de SMTP mantém pedido e permite reenvio sem novo cadastro',async t=>{
  let fail=true;
  const app=createApp({dbPath:':memory:',mailConfig:{ready:true,to:'empresa@example.com',from:'site@example.com'},transport:{sendMail:async()=>{if(fail)throw Object.assign(new Error('simulado'),{code:'EAUTH'});return {accepted:['empresa@example.com']};}}});
  const base=await authenticatedBase(app); t.after(()=>app.stop());
  const c=(await request(base,'clientes','POST',cliente)).body;
  const p=(await request(base,'solicitacoes-orcamento','POST',pedido(c.id))).body;
  await app.mailer.flush();
  const row=app.db.prepare('SELECT * FROM outbox').get(); assert.equal(row.status,'FALHOU');
  assert.equal((await request(base,`solicitacoes-orcamento/${p.id}`)).res.status,200);
  fail=false; app.db.prepare('UPDATE outbox SET proximaTentativa=0').run(); await app.mailer.flush();
  assert.equal(app.db.prepare('SELECT status FROM outbox').get().status,'ENVIADO');
});

test('persistência após reiniciar e envio pendente usa a configuração atual',async t=>{
  const dir=mkdtempSync(join(tmpdir(),'doni-test-'));
  const dbPath=join(dir,'test.sqlite');
  let app=createApp({dbPath,mailConfig:{ready:false,to:'antes@example.com'}});
  t.after(async()=>{ await app.stop(); rmSync(dir,{recursive:true,force:true}); });
  let base=await authenticatedBase(app);
  const c=(await request(base,'clientes','POST',cliente)).body;
  const p=(await request(base,'solicitacoes-orcamento','POST',pedido(c.id))).body;
  await app.stop();
  const sent=[];
  app=createApp({dbPath,mailConfig:{ready:true,to:'atual@example.com',from:'site@example.com'},transport:{sendMail:async msg=>{sent.push(msg);return {accepted:['atual@example.com']};}}});
  base=await authenticatedBase(app);
  await app.mailer.flush();
  assert.equal(sent.length,1); assert.equal(sent[0].to,'atual@example.com'); assert.equal(sent[0].from.address,'site@example.com');
  const r=await request(base,`solicitacoes-orcamento/${p.id}`); assert.equal(r.res.status,200); assert.equal(r.body.statusEmail,'ENVIADO');
});

test('mock responde conforme o contrato, com IDs dinâmicos e DELETE vazio',async t=>{
  const server=createMock(); await new Promise(r=>server.listen(0,'127.0.0.1',r));
  t.after(()=>new Promise(r=>server.close(r)));
  const base=`http://127.0.0.1:${server.address().port}`;
  const a=await request(base,'clientes'), b=await request(base,'clientes');
  conforms('ListaClientes',a.body); assert.notEqual(a.body.dados[0].id,b.body.dados[0].id);
  const c=await request(base,'clientes','POST',cliente); assert.equal(c.res.status,201); conforms('Cliente',c.body);
  const deleted=await request(base,`clientes/${c.body.id}`,'DELETE'); assert.equal(deleted.res.status,204);
});
