import { writeFileSync } from 'node:fs';
import { contract } from '../validation.mjs';
import { buildMessage } from '../mail.mjs';

const cliente=contract.paths['/api/v1/clientes'].post.responses['201'].content['application/json'].example;
const pedido=contract.paths['/api/v1/solicitacoes-orcamento'].post.responses['201'].content['application/json'].example;
const message=buildMessage(cliente,pedido,{to:'yuri.taka6@gmail.com',from:'site@example.com'});
writeFileSync(new URL('../docs/email-exemplo.html',import.meta.url),`<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Prévia fictícia — e-mail Doni Transportes</title></head><body><p style="font:16px Arial;text-align:center;background:#fff3cd;padding:16px">Prévia com dados fictícios. Nenhum e-mail foi enviado.</p>${message.html}</body></html>`);
console.log('Prévia salva em docs/email-exemplo.html. Nenhum e-mail foi enviado.');
