import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../cloudflare/worker.mjs';

test('proxy preserva DELETE 204 sem corpo e converte página de inicialização em problema JSON',async()=>{
 const original=globalThis.fetch;
 try{
  globalThis.fetch=async()=>new Response(null,{status:204});
  const deleted=await worker.fetch(new Request('https://donitransportes.com.br/api/v1/clientes/test',{method:'DELETE'}),{API_ORIGIN:'https://example.com'});
  assert.equal(deleted.status,204);assert.equal(await deleted.text(),'');
  globalThis.fetch=async()=>new Response('<html>Starting</html>',{status:503,headers:{'Content-Type':'text/html'}});
  const pending=await worker.fetch(new Request('https://donitransportes.com.br/api/v1/clientes'),{API_ORIGIN:'https://example.com'});
  assert.equal(pending.status,503);assert.match(pending.headers.get('Content-Type'),/problem\+json/);assert.equal((await pending.json()).status,503);
 }finally{globalThis.fetch=original;}
});
