import { DatabaseSync } from 'node:sqlite';
import { readFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { drizzle } from 'drizzle-orm/node-sqlite';
import { eq, and, ne, lte, asc, desc, count, sql } from 'drizzle-orm';
import * as tables from './schema.mjs';

const root=fileURLToPath(new URL('../../',import.meta.url));
export function openDatabase(path=resolve(root,'data/doni.sqlite')) {
  if(path!==':memory:')mkdirSync(dirname(path),{recursive:true});
  const client=new DatabaseSync(path);
  client.exec('PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000; CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, appliedAt TEXT NOT NULL)');
  try {
    for(const name of readdirSync(resolve(root,'migrations')).filter(n=>n.endsWith('.sql')).sort()) {
      if(client.prepare('SELECT 1 FROM schema_migrations WHERE name=?').get(name))continue;
      client.exec('BEGIN');
      try {client.exec(readFileSync(resolve(root,'migrations',name),'utf8'));client.prepare('INSERT INTO schema_migrations VALUES (?,?)').run(name,new Date().toISOString());client.exec('COMMIT');}
      catch(error){client.exec('ROLLBACK');throw error;}
    }
  } catch(error){client.close();throw error;}
  const orm=drizzle({client});
  return {client,orm,repo:createRepository(orm)};
}
export function createRepository(orm) {
  const tableFor=name=>{if(!['clientes','solicitacoes'].includes(name))throw new Error('Tabela inválida');return tables[name];};
  return {
    orm,
    find(name,id){const t=tableFor(name);const item=orm.select().from(t).where(eq(t.id,id)).get()?.dados;if(item&&name==='solicitacoes')item.statusEmail=orm.select().from(tables.outbox).where(eq(tables.outbox.solicitacaoId,id)).get()?.status||'PENDENTE';return item;},
    insert(name,item){const t=tableFor(name);orm.insert(t).values({id:item.id,dados:item,...(name==='solicitacoes'?{clienteId:item.clienteId}:{})}).run();},
    update(name,item){const t=tableFor(name);orm.update(t).set({dados:item}).where(eq(t.id,item.id)).run();},
    delete(name,id){const t=tableFor(name);orm.delete(t).where(eq(t.id,id)).run();},
    hasPedidos(id){return Boolean(orm.select({id:tables.solicitacoes.id}).from(tables.solicitacoes).where(eq(tables.solicitacoes.clienteId,id)).limit(1).get());},
    list(name,{pagina,limite,busca,status,clienteId}){
      const t=tableFor(name),conditions=[];
      if(busca!==null&&busca!==undefined)conditions.push(sql`instr(lower(json_extract(${t.dados}, '$.nome')),lower(${busca})) > 0`);
      if(status!==null&&status!==undefined)conditions.push(eq(sql`json_extract(${t.dados}, '$.status')`,status));
      if(clienteId!==null&&clienteId!==undefined)conditions.push(eq(t.clienteId,clienteId));
      const where=conditions.length?and(...conditions):undefined;
      const total=orm.select({n:count()}).from(t).where(where).get().n;
      const rows=orm.select({id:t.id}).from(t).where(where).orderBy(desc(sql`json_extract(${t.dados}, '$.criadoEm')`),asc(t.id)).limit(limite).offset((pagina-1)*limite).all();
      return {ids:rows.map(r=>r.id),total};
    },
    transaction(fn){return orm.transaction(tx=>fn(createRepository(tx)));},
    enqueue(cliente,pedido){orm.insert(tables.outbox).values({solicitacaoId:pedido.id,payload:{cliente,pedido},status:'PENDENTE',tentativas:0,proximaTentativa:0}).run();},
    pending(){return orm.select().from(tables.outbox).where(and(ne(tables.outbox.status,'ENVIADO'),lte(tables.outbox.proximaTentativa,Date.now()))).orderBy(asc(tables.outbox.proximaTentativa)).limit(10).all();},
    markSent(id){orm.update(tables.outbox).set({status:'ENVIADO',tentativas:sql`${tables.outbox.tentativas}+1`,ultimoErro:null}).where(eq(tables.outbox.solicitacaoId,id)).run();},
    markFailed(id,code,next){orm.update(tables.outbox).set({status:'FALHOU',tentativas:sql`${tables.outbox.tentativas}+1`,ultimoErro:code,proximaTentativa:next}).where(eq(tables.outbox.solicitacaoId,id)).run();},
  };
}
