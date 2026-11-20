import {mkdirSync,copyFileSync} from 'node:fs';
mkdirSync('dist',{recursive:true});
for(const file of ['index.html','sobre.html','servicos.html','orcamento.html','orcamento.js','orcamento.css','contato.js','admin.html','admin.js','branding.css','logo-doni.jpeg','logo-doni-transparente.png','caminhao2.jpeg','caminhaobau.jpeg','caminhaofrentepla.jpeg','caminhaolado.jpeg'])copyFileSync(file,'dist/'+file);
console.log('Assets públicos preparados; nenhum segredo, código Python ou banco incluído.');
