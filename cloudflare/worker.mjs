// Assets ficam na Cloudflare; toda regra de negócio é executada no FastAPI.
const failure=(path,status,detail)=>Response.json({type:'https://donitransportes.com.br/problems/service-unavailable',title:'Serviço indisponível',status,detail,instance:path,invalidParams:[]},{status,headers:{'Content-Type':'application/problem+json','Cache-Control':'no-store'}});
export default {
 async fetch(request,env){
  const url=new URL(request.url);
  if(!url.pathname.startsWith('/api/')&&!['/openapi.json','/health'].includes(url.pathname))return env.ASSETS.fetch(request);
  if(!env.API_ORIGIN)return failure(url.pathname,503,'O atendimento está em configuração. Tente novamente em instantes.');
  const target=new URL(url.pathname+url.search,env.API_ORIGIN);
  const headers=new Headers(request.headers);
  headers.delete('host');headers.delete('cookie');headers.delete('x-doni-proxy-key');headers.delete('x-doni-client-ip');
  headers.set('x-doni-proxy-key',env.PROXY_SECRET||'');headers.set('x-doni-client-ip',request.headers.get('CF-Connecting-IP')||'');
  try {
   const response=await fetch(target,{method:request.method,headers,body:['GET','HEAD'].includes(request.method)?undefined:request.body,redirect:'manual',signal:AbortSignal.timeout(90000)});
   if(response.status===204)return new Response(null,{status:204,headers:{'Cache-Control':'no-store'}});
   const type=response.headers.get('Content-Type')||'';
   if(!type.includes('json'))return failure(url.pathname,503,'O serviço está iniciando. Aguarde um minuto e tente novamente.');
   const outgoing=new Response(response.body,response);outgoing.headers.set('Cache-Control','no-store');return outgoing;
  }catch{return failure(url.pathname,503,'Não foi possível conectar ao atendimento. Aguarde alguns instantes e tente novamente.');}
 }
};
