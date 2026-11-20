// Mock sem persistência e sem envio de e-mails. Usa os exemplos do contrato.
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { contract } from './validation.mjs';

export function createMock() {
  const server = createServer((req,res) => {
    const path = new URL(req.url,'http://127.0.0.1').pathname;
    let operation, pathId;
    for (const [template,item] of Object.entries(contract.paths)) {
      const match = path.match(new RegExp('^'+template.replace('{id}','([^/]+)')+'$'));
      if (match) { operation = item[req.method.toLowerCase()]; pathId = match[1]; break; }
    }
    const status = operation ? Number(Object.keys(operation.responses).find(s=>Number(s)<300)) : 404;
    if (!operation) {
      res.writeHead(404,{'Content-Type':'application/json'});
      return res.end(JSON.stringify({status:404,codigo:'NAO_ENCONTRADO',mensagem:'Rota de mock não encontrada.',detalhes:[],instante:new Date().toISOString()}));
    }
    const definition = operation.responses[status];
    const sample = structuredClone(definition.content?.['application/json']?.example);
    if (sample) {
      const records = sample.dados || [sample];
      for (const record of records) {
        if ('id' in record) record.id = pathId || randomUUID();
        if ('criadoEm' in record) record.criadoEm = new Date().toISOString();
        if ('atualizadoEm' in record) record.atualizadoEm = new Date().toISOString();
      }
    }
    const headers = status===204 ? {} : {'Content-Type':'application/json; charset=utf-8'};
    if (status===201) headers.Location = `${path}/${sample.id}`;
    res.writeHead(status,headers);
    res.end(sample ? JSON.stringify(sample) : undefined);
  });
  return server;
}

if (process.argv[1]?.endsWith('mock-server.mjs')) {
  const port = Number(process.env.MOCK_PORT || 3001);
  createMock().listen(port,'127.0.0.1',()=>console.log(`Mock local: http://127.0.0.1:${port} — sem persistência ou e-mail.`));
}
