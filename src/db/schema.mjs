import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';

// Modelo híbrido preservado da Parte 1: dados de domínio em JSON, identidade e vínculo relacionais.
export const clientes = sqliteTable('clientes', { id:text().primaryKey(), dados:text({mode:'json'}).notNull() });
export const solicitacoes = sqliteTable('solicitacoes', {
  id:text().primaryKey(), clienteId:text().notNull().references(()=>clientes.id,{onDelete:'restrict'}), dados:text({mode:'json'}).notNull(),
}, table=>[index('idx_solicitacoes_cliente').on(table.clienteId)]);
export const outbox = sqliteTable('outbox', {
  solicitacaoId:text().primaryKey().references(()=>solicitacoes.id,{onDelete:'cascade'}), payload:text({mode:'json'}).notNull(),
  status:text().notNull(),tentativas:integer().notNull(),proximaTentativa:integer().notNull(),ultimoErro:text(),
});
export const usuarios = sqliteTable('usuarios', {
  id:text().primaryKey(),email:text().notNull().unique(),nome:text().notNull(),senhaHash:text().notNull(),papel:text({enum:['ADMIN','LEITOR']}).notNull(),criadoEm:text().notNull(),
});
export const sessoes = sqliteTable('sessoes', {
  tokenHash:text().primaryKey(),usuarioId:text().notNull().references(()=>usuarios.id,{onDelete:'cascade'}),expiraEm:integer().notNull(),
},table=>[index('idx_sessoes_expira').on(table.expiraEm)]);
