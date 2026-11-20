import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,sep} from 'node:path';
import {openDatabase} from '../src/db/database.mjs';
import {createApp} from '../server.mjs';
import {verifyPassword} from '../src/auth.mjs';

const password='SomenteNosTestes123!';
async function setup(t,options={}){const app=createApp({dbPath:':memory:',mailConfig:{ready:false},...options});const base=await app.start(0);t.after(()=>app.stop());return {app,base};}
async function login(base,email='admin@example.com',senha=password){return fetch(base+'/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,senha})});}

test('AUTH-01/02/04: senha derivada, cookie seguro e rotas protegidas',async t=>{
 const {app,base}=await setup(t);await app.auth.createUser({nome:'Admin',email:'admin@example.com',password});
 const stored=app.db.prepare('SELECT * FROM usuarios').get();assert.notEqual(stored.senhaHash,password);assert.ok(stored.senhaHash.startsWith('scrypt$'));assert.ok(await verifyPassword(password,stored.senhaHash));
 assert.equal((await fetch(base+'/api/v1/clientes')).status,401);
 assert.equal((await login(base,'inexistente@example.com')).status,401);assert.equal((await login(base,'admin@example.com','errada')).status,401);
 const response=await login(base);assert.equal(response.status,200);const cookie=response.headers.get('set-cookie');assert.match(cookie,/HttpOnly/);assert.match(cookie,/SameSite=Strict/);assert.match(cookie,/Max-Age=28800/);
 const user=await response.json();assert.equal(user.usuario.papel,'ADMIN');assert.ok(!JSON.stringify(user).includes('senhaHash'));
 const raw=cookie.split(';')[0],token=raw.split('=')[1],session=app.db.prepare('SELECT * FROM sessoes').get();assert.equal(session.tokenHash,createHash('sha256').update(token).digest('hex'));assert.notEqual(session.tokenHash,token);
 assert.equal((await fetch(base+'/api/v1/clientes',{headers:{Cookie:raw}})).status,200);
 assert.equal((await fetch(base+'/api/v1/auth/me',{headers:{Cookie:raw}})).status,200);
 assert.equal((await fetch(base+'/api/v1/auth/me',{headers:{Cookie:'doni_session=invalido'}})).status,401);
 assert.equal((await fetch(base+'/api/v1/auth/logout',{method:'POST',headers:{Cookie:raw,Origin:'https://outro.example'}})).status,403);
});
test('AUTH-02: LEITOR consulta mas não pode alterar ou excluir',async t=>{
 const {app,base}=await setup(t);await app.auth.createUser({nome:'Leitor',email:'leitor@example.com',password,papel:'LEITOR'});
 const cookie=(await login(base,'leitor@example.com')).headers.get('set-cookie').split(';')[0];
 const created=await fetch(base+'/api/v1/clientes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome:'Cliente',email:'cliente@example.com',telefone:'+5516991234567'})});assert.equal(created.status,201);const client=await created.json();
 assert.equal((await fetch(base+'/api/v1/clientes',{headers:{Cookie:cookie}})).status,200);
 for(const method of ['PATCH','DELETE'])assert.equal((await fetch(base+'/api/v1/clientes/'+client.id,{method,headers:{Cookie:cookie,'Content-Type':'application/json'},body:method==='PATCH'?JSON.stringify({nome:'Outro'}):undefined})).status,403);
});
test('AUTH-03: logout revoga no banco e expiração é verificada',async t=>{
 let now=Date.now();const {app,base}=await setup(t,{clock:()=>now});await app.auth.createUser({nome:'Admin',email:'admin@example.com',password});
 let cookie=(await login(base)).headers.get('set-cookie').split(';')[0];
 const logout=await fetch(base+'/api/v1/auth/logout',{method:'POST',headers:{Cookie:cookie}});assert.equal(logout.status,204);assert.match(logout.headers.get('set-cookie'),/Max-Age=0/);
 assert.equal((await fetch(base+'/api/v1/clientes',{headers:{Cookie:cookie}})).status,401);
 cookie=(await login(base)).headers.get('set-cookie').split(';')[0];now+=8*3600000+1;
 assert.equal((await fetch(base+'/api/v1/clientes',{headers:{Cookie:cookie}})).status,401);
});
test('AUTH-05: bloqueia a sexta falha de login e retorna Retry-After',async t=>{
 const {base}=await setup(t);for(let i=0;i<5;i++)assert.equal((await login(base,'ninguem@example.com','errada')).status,401);
 const limited=await login(base);assert.equal(limited.status,429);assert.equal(limited.headers.get('retry-after'),'900');
});
test('ORM-02: migrações idempotentes e conta sem senha padrão',async t=>{
 const {app}=await setup(t);assert.equal(app.db.prepare('SELECT count(*) AS n FROM schema_migrations').get().n,2);assert.equal(app.db.prepare('SELECT count(*) AS n FROM usuarios').get().n,0);
 await assert.rejects(()=>app.auth.createUser({nome:'Admin',email:'admin@example.com',password:'123'}));
});
test('AUTH-03: produção marca o cookie como Secure e usa prefixo __Host-',async t=>{
 const {app,base}=await setup(t,{secureCookies:true});await app.auth.createUser({nome:'Admin',email:'admin@example.com',password});
 const response=await login(base);assert.match(response.headers.get('set-cookie'),/^__Host-doni_session=/);assert.match(response.headers.get('set-cookie'),/; Secure/);
});
test('ORM-01/02: migra banco legado sem perder dados; rollback desfaz pedido e fila',()=>{
 const dir=mkdtempSync(join(tmpdir(),'doni-migration-'));assert.ok(resolve(dir).startsWith(resolve(tmpdir())+sep));
 const file=join(dir,'legacy.sqlite');let database;
 try{
  const old=new DatabaseSync(file);old.exec('CREATE TABLE clientes (id TEXT PRIMARY KEY,dados TEXT NOT NULL)');
  old.prepare('INSERT INTO clientes VALUES (?,?)').run('legado',JSON.stringify({id:'legado',nome:'Cliente preservado'}));old.close();
  database=openDatabase(file);assert.equal(database.repo.find('clientes','legado').nome,'Cliente preservado');database.client.close();
  database=openDatabase(file);assert.equal(database.client.prepare('SELECT count(*) AS n FROM schema_migrations').get().n,2);
  assert.throws(()=>database.repo.transaction(tx=>{tx.insert('solicitacoes',{id:'rollback',clienteId:'legado'});throw new Error('Falha simulada antes da fila');}));
  assert.equal(database.repo.find('solicitacoes','rollback'),undefined);
 }finally{database?.client.close();rmSync(dir,{recursive:true,force:true});}
});
