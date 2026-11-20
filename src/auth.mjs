import { randomBytes, randomUUID, scrypt, timingSafeEqual, createHash } from 'node:crypto';
import { promisify } from 'node:util';
import { eq, lte } from 'drizzle-orm';
import { usuarios, sessoes } from './db/schema.mjs';

const derive=promisify(scrypt);
const digest=token=>createHash('sha256').update(token).digest('hex');
export async function hashPassword(password){const salt=randomBytes(16).toString('hex');return `scrypt$${salt}$${(await derive(password,salt,64)).toString('hex')}`;}
export async function verifyPassword(password,encoded){const [scheme,salt,hash]=encoded.split('$');if(scheme!=='scrypt'||!salt||!hash)return false;const expected=Buffer.from(hash,'hex'),actual=await derive(password,salt,64);return actual.length===expected.length&&timingSafeEqual(actual,expected);}
const publicUser=user=>({id:user.id,nome:user.nome,email:user.email,papel:user.papel});
export function createAuth(orm,{secure=false,clock=Date.now}={}){
  const cookieName=secure?'__Host-doni_session':'doni_session';
  let dummyHash;
  const tokenFrom=req=>{const raw=(req.headers.cookie||'').split(';').map(s=>s.trim()).find(s=>s.startsWith(cookieName+'='))?.slice(cookieName.length+1);return raw&&/^[a-f0-9]{64}$/.test(raw)?raw:null;};
  const cookie=(token,seconds)=>`${cookieName}=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${seconds}${secure?'; Secure':''}`;
  return {
    async createUser({email,nome,password,papel='ADMIN'}){
      if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||email.length>254||password.length<12||password.length>128||!nome.trim()||nome.length>120||!['ADMIN','LEITOR'].includes(papel))throw new Error('Informe e-mail válido, nome e senha de 12 a 128 caracteres.');
      const user={id:randomUUID(),email:email.trim().toLowerCase(),nome:nome.trim(),senhaHash:await hashPassword(password),papel,criadoEm:new Date(clock()).toISOString()};
      orm.insert(usuarios).values(user).run();return publicUser(user);
    },
    async login(email,password){
      const user=orm.select().from(usuarios).where(eq(usuarios.email,email.trim().toLowerCase())).get();
      dummyHash??=hashPassword(randomBytes(32).toString('hex'));
      const valid=await verifyPassword(password,user?.senhaHash||await dummyHash);
      if(!user||!valid)return null;
      const token=randomBytes(32).toString('hex');
      orm.delete(sessoes).where(lte(sessoes.expiraEm,clock())).run();
      orm.insert(sessoes).values({tokenHash:digest(token),usuarioId:user.id,expiraEm:clock()+8*3600000}).run();
      return {usuario:publicUser(user),cookie:cookie(token,8*3600)};
    },
    current(req){const token=tokenFrom(req);if(!token)return null;const session=orm.select().from(sessoes).where(eq(sessoes.tokenHash,digest(token))).get();if(!session||session.expiraEm<=clock())return null;const user=orm.select().from(usuarios).where(eq(usuarios.id,session.usuarioId)).get();return user?publicUser(user):null;},
    logout(req){const token=tokenFrom(req);if(token)orm.delete(sessoes).where(eq(sessoes.tokenHash,digest(token))).run();return cookie('',0);},
  };
}

export function createLimiter(){
  const entries=new Map();
  return {check(key,max,windowMs){const now=Date.now();for(const [k,v]of entries)if(v.until<=now)entries.delete(k);let item=entries.get(key);if(!item){item={count:0,until:now+windowMs};entries.set(key,item);}return ++item.count<=max;},reset(key){entries.delete(key);}};
}
