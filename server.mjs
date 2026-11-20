import { createServer } from 'node:http';
import { openDatabase } from './src/db/database.mjs';
import { createAuth, createLimiter } from './src/auth.mjs';
import { randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, resolve, extname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { contract, validate, validators } from './validation.mjs';
import { createMailer } from './mail.mjs';

const root = dirname(fileURLToPath(import.meta.url));
const now = () => new Date().toISOString();
class ApiFailure extends Error {
  constructor(status, codigo, mensagem, detalhes = []) { super(mensagem); Object.assign(this, { status, codigo, detalhes }); }
}
const fail = (status, code, message, details) => { throw new ApiFailure(status, code, message, details); };
const validId = value => validators.Identificador(value);
const staticFiles = new Set(['index.html','sobre.html','servicos.html','orcamento.html','orcamento.js','orcamento.css','contato.js','admin.html','admin.js','caminhao2.jpeg','caminhaobau.jpeg','caminhaofrentepla.jpeg','caminhaolado.jpeg']);
const mime = { '.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.jpeg':'image/jpeg' };

export function createApp(options = {}) {
  const dbFile = options.dbPath || process.env.DB_PATH || resolve(root, 'data/doni.sqlite');
  if (dbFile !== ':memory:') mkdirSync(dirname(dbFile), { recursive:true });
  const {client:db,orm,repo}=openDatabase(dbFile);
  const auth=createAuth(orm,{secure:options.secureCookies ?? process.env.NODE_ENV==='production',clock:options.clock});
  const limiter=createLimiter();
  const mailer = createMailer(repo, options.mailConfig, options.transport);
  const json = (res, status, value, headers = {}) => {
    res.writeHead(status, { 'Content-Type':'application/json; charset=utf-8', 'Cache-Control':'no-store', ...headers });
    res.end(status === 204 ? undefined : JSON.stringify(value));
  };
  function get(table, id) {
    const item=repo.find(table,id);
    if(!item)fail(404,'NAO_ENCONTRADO','Recurso não encontrado.');
    return item;
  }
  async function readBody(req, schema) {
    if (req.headers['content-type']?.split(';')[0].trim().toLowerCase() !== 'application/json') fail(415,'MIDIA_NAO_SUPORTADA','Use Content-Type application/json.');
    let size = 0;
    const chunks = [];
    for await (const chunk of req) {
      size += chunk.length;
      if (size > 65536) { req.resume(); fail(413,'CORPO_MUITO_GRANDE','O corpo excede 64 KiB.'); }
      chunks.push(chunk);
    }
    let body;
    try { body = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
    catch { fail(400,'REQUISICAO_INVALIDA','JSON inválido.'); }
    const errors = validate(schema, body);
    if (errors.length) fail(422,'VALIDACAO','Os dados enviados são inválidos.',errors);
    return body;
  }
  const server = createServer(async (req,res) => {
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Referrer-Policy','strict-origin-when-cross-origin');
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      const pathname = decodeURIComponent(url.pathname);
      // Nenhum arquivo fora da lista pública é exposto (.env, SQLite e código ficam privados).
      if (!pathname.startsWith('/api/')) {
        if (!['GET','HEAD'].includes(req.method)) fail(405,'METODO_NAO_PERMITIDO','Método não permitido.');
        if (pathname === '/openapi.json') return json(res,200,contract);
        if (pathname === '/openapi-v1.json') return json(res,200,JSON.parse(readFileSync(resolve(root,'docs/openapi.json'),'utf8')));
        const file = pathname === '/' ? 'index.html' : pathname.slice(1);
        if (!staticFiles.has(file) || !existsSync(resolve(root,file))) fail(404,'NAO_ENCONTRADO','Página não encontrada.');
        res.writeHead(200, { 'Content-Type':mime[extname(file)] || 'application/octet-stream' });
        return res.end(req.method === 'HEAD' ? undefined : readFileSync(resolve(root,file)));
      }
      const mutation=!['GET','HEAD','OPTIONS'].includes(req.method);
      if(mutation&&req.headers.origin&&!['http://'+req.headers.host,'https://'+req.headers.host].includes(req.headers.origin))fail(403,'PROIBIDO','Origem da requisição não permitida.');
      const authPath=pathname.match(/^\/api\/v1\/auth\/(login|me|logout)$/)?.[1];
      if(authPath){
        if(authPath==='login'&&req.method==='POST'){
          const key='login:'+req.socket.remoteAddress;
          if(!limiter.check(key,5,15*60000)){res.setHeader('Retry-After','900');fail(429,'LIMITE_EXCEDIDO','Muitas tentativas. Tente novamente mais tarde.');}
          const input=await readBody(req,'LoginDTO');
          const result=await auth.login(input.email,input.senha);
          if(!result)fail(401,'NAO_AUTENTICADO','E-mail ou senha inválidos.');
          limiter.reset(key);
          return json(res,200,{usuario:result.usuario},{'Set-Cookie':result.cookie});
        }
        if(authPath==='me'&&req.method==='GET'){
          const usuario=auth.current(req);
          if(!usuario)fail(401,'NAO_AUTENTICADO','Entre para continuar.');
          return json(res,200,{usuario});
        }
        if(authPath==='logout'&&req.method==='POST')return json(res,204,undefined,{'Set-Cookie':auth.logout(req)});
        fail(405,'METODO_NAO_PERMITIDO','Método não permitido nesta rota.');
      }
      const match = pathname.match(/^\/api\/v1\/(clientes|solicitacoes-orcamento)(?:\/([^/]+))?$/);
      if (!match) fail(404,'NAO_ENCONTRADO','Rota não encontrada.');
      const [,resource,id] = match;
      const isCliente = resource === 'clientes';
      const table = isCliente ? 'clientes' : 'solicitacoes';
      const model = isCliente ? 'Cliente' : 'Solicitacao';
      const publicCreation=req.method==='POST'&&!id;
      if(!publicCreation){
        const user=auth.current(req);
        if(!user)fail(401,'NAO_AUTENTICADO','Entre para continuar.');
        if(!['GET','HEAD'].includes(req.method)&&user.papel!=='ADMIN')fail(403,'PROIBIDO','Seu perfil permite apenas consultas.');
      } else if(!limiter.check('form:'+req.socket.remoteAddress,30,60000)){
        res.setHeader('Retry-After','60');fail(429,'LIMITE_EXCEDIDO','Muitas solicitações. Tente novamente em um minuto.');
      }
      if (id && !validId(id)) fail(400,'REQUISICAO_INVALIDA','O identificador deve ser um UUID válido.');
      if (req.method === 'GET' && !id) {
        const allowed = ['pagina','limite',...(isCliente ? ['busca'] : ['status','clienteId'])];
        for (const key of url.searchParams.keys()) {
          if (!allowed.includes(key) || url.searchParams.getAll(key).length !== 1) fail(400,'REQUISICAO_INVALIDA','Parâmetro desconhecido ou repetido.');
        }
        function integer(key, fallback, max) {
          const raw = url.searchParams.get(key);
          if (raw === null) return fallback;
          if (!/^[1-9]\d*$/.test(raw) || Number(raw) > max) fail(400,'REQUISICAO_INVALIDA',`Parâmetro ${key} inválido.`);
          return Number(raw);
        }
        const pagina = integer('pagina',1,1000000), limite = integer('limite',20,100);

        const search = url.searchParams.get('busca');
        if (search !== null) {
          if (!validators.BuscaParametro(search)) fail(400,'REQUISICAO_INVALIDA','Busca inválida.');

        }
        const status = url.searchParams.get('status');
        if (status !== null) {
          if (!contract.components.schemas.StatusSolicitacao.enum.includes(status)) fail(400,'REQUISICAO_INVALIDA','Status inválido.');

        }
        const clienteId = url.searchParams.get('clienteId');
        if (clienteId !== null) {
          if (!validId(clienteId)) fail(400,'REQUISICAO_INVALIDA','clienteId deve ser um UUID.');

        }
        const {ids,total}=repo.list(table,{pagina,limite,busca:search,status,clienteId});
        return json(res,200,{dados:ids.map(id=>get(table,id)),paginacao:{pagina,limite,total,totalPaginas:Math.ceil(total/limite)}});
      }
      if (req.method === 'GET' && id) return json(res,200,get(table,id));
      if (req.method === 'POST' && !id) {
        const body = await readBody(req,`Create${model}DTO`);
        const time = now();
        const item = { ...body, id:randomUUID(), criadoEm:time, atualizadoEm:time };
        if (isCliente) {
          item.tipoPessoa ??= 'PF';
          repo.insert('clientes',item);
        } else {
          const clienteRow = repo.find('clientes',body.clienteId);
          if (!clienteRow) fail(422,'VALIDACAO','Cliente vinculado não existe.',[{ campo:'/clienteId',mensagem:'Cadastre o cliente antes de solicitar o orçamento.' }]);
          item.observacoes ??= null;
          item.status = 'RECEBIDA'; item.statusEmail = 'PENDENTE';
          repo.transaction(tx=>{tx.insert('solicitacoes',item);tx.enqueue(clienteRow,item);});
          setImmediate(() => void mailer.flush());
        }
        return json(res,201,item,{ Location:`/api/v1/${resource}/${item.id}` });
      }
      if (req.method === 'PATCH' && id) {
        const previous = get(table,id);
        const body = await readBody(req,`Update${model}DTO`);
        const item = { ...previous,...body,atualizadoEm:now() };
        repo.update(table,item);
        return json(res,200,item);
      }
      if (req.method === 'DELETE' && id) {
        get(table,id);
        if (isCliente && repo.hasPedidos(id)) fail(409,'CONFLITO','Cliente possui solicitações vinculadas.');
        repo.delete(table,id);
        return json(res,204);
      }
      res.setHeader('Allow',id ? 'GET, PATCH, DELETE' : 'GET, POST');
      fail(405,'METODO_NAO_PERMITIDO','Método não permitido nesta rota.');
    } catch (error) {
      if (res.headersSent || res.destroyed) return;
      if (error instanceof URIError) error = new ApiFailure(400,'REQUISICAO_INVALIDA','URL inválida.');
      const known = error instanceof ApiFailure;
      if (!known) console.error('Falha interna:',error.code || error.name);
      json(res,known ? error.status : 500,{ status:known ? error.status : 500, codigo:known ? error.codigo : 'ERRO_INTERNO', mensagem:known ? error.message : 'Não foi possível concluir a operação.', detalhes:known ? error.detalhes : [], instante:now() });
    }
  });
  server.requestTimeout = 30000;
  return {
    server, db, orm, repo, auth, mailer,
    async start(port = 3000) {
      await new Promise((resolve,reject) => { server.once('error',reject); server.listen(port,'127.0.0.1',resolve); });
      mailer.start();
      return `http://127.0.0.1:${server.address().port}`;
    },
    async stop() {
      await new Promise(resolve => server.close(resolve));
      await mailer.stop(); db.close();
    },
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const app = createApp();
  console.log(`Doni Transportes: ${await app.start(Number(process.env.PORT || 3000))}`);
  if (!process.env.SMTP_PASS) console.log('SMTP não configurado: pedidos serão salvos e e-mails ficarão pendentes.');
  for (const signal of ['SIGINT','SIGTERM']) process.once(signal,async () => { await app.stop(); process.exit(0); });
}
