CREATE TABLE IF NOT EXISTS clientes (id TEXT PRIMARY KEY, dados TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS solicitacoes (id TEXT PRIMARY KEY, clienteId TEXT NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT, dados TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_cliente ON solicitacoes(clienteId);
CREATE TABLE IF NOT EXISTS outbox (solicitacaoId TEXT PRIMARY KEY REFERENCES solicitacoes(id) ON DELETE CASCADE,
  payload TEXT NOT NULL, status TEXT NOT NULL, tentativas INTEGER NOT NULL, proximaTentativa INTEGER NOT NULL, ultimoErro TEXT);
