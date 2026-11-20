CREATE TABLE usuarios (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, nome TEXT NOT NULL,
  senhaHash TEXT NOT NULL, papel TEXT NOT NULL CHECK (papel IN ('ADMIN','LEITOR')), criadoEm TEXT NOT NULL);
CREATE TABLE sessoes (tokenHash TEXT PRIMARY KEY, usuarioId TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE, expiraEm INTEGER NOT NULL);
CREATE INDEX idx_sessoes_expira ON sessoes(expiraEm);
