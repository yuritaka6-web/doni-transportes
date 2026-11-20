import { createInterface } from 'node:readline/promises';
import { Writable } from 'node:stream';
import { openDatabase } from '../src/db/database.mjs';
import { createAuth } from '../src/auth.mjs';

if(!process.stdin.isTTY){console.error('Execute este comando em um terminal interativo. Não passe a senha como argumento.');process.exit(1);}
let hidden=false;
const output=new Writable({write(chunk,encoding,callback){if(!hidden)process.stdout.write(chunk,encoding);callback();}});
const input=createInterface({input:process.stdin,output,terminal:true});
let database;
try {
  const email=(process.argv[2]||await input.question('E-mail do administrador: ')).trim();
  const nome=await input.question('Nome do administrador: ');
  process.stdout.write('Senha (12 a 128 caracteres; a digitacao fica oculta): ');
  hidden=true;const password=await input.question('');hidden=false;process.stdout.write('\n');
  process.stdout.write('Repita a senha: ');hidden=true;const confirmation=await input.question('');hidden=false;process.stdout.write('\n');
  if(password!==confirmation)throw new Error('As senhas não coincidem.');
  database=openDatabase(process.env.DB_PATH);
  await createAuth(database.orm).createUser({email,nome,password});
  console.log('Administrador criado. Entre em http://127.0.0.1:3000/admin.html');
}catch(error){console.error(error.message.includes('UNIQUE')?'Este e-mail já tem uma conta.':error.message);process.exitCode=1;}
finally{hidden=false;input.close();database?.client.close();}
