"""Comandos locais. Nunca imprimir credenciais, hashes ou dados de contatos."""
import argparse
import getpass
import json
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import select
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api.main import app
from src.api.database import initialize
from src.api.models import ClienteModel, SolicitacaoModel, OutboxModel, UserModel
from src.api.security import hash_password


def import_legacy(source_path, sessions):
    source = sqlite3.connect(f"file:{Path(source_path).resolve().as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    counts = {"clientes": 0, "solicitacoes": 0, "usuarios": 0}
    try:
        with sessions() as db:
            for row in source.execute("SELECT * FROM clientes"):
                data = json.loads(row["dados"])
                if not db.get(ClienteModel, row["id"]):
                    db.add(ClienteModel(id=row["id"], nome=data["nome"], email=data["email"], telefone=data["telefone"], tipo_pessoa=data.get("tipoPessoa", "PF"), criado_em=datetime.fromisoformat(data["criadoEm"]), atualizado_em=datetime.fromisoformat(data["atualizadoEm"])))
                    counts["clientes"] += 1
            db.flush()
            for row in source.execute("SELECT * FROM solicitacoes"):
                data = json.loads(row["dados"])
                if not db.get(SolicitacaoModel, row["id"]):
                    db.add(SolicitacaoModel(id=row["id"], cliente_id=row["clienteId"], origem_cidade=data["origem"]["cidade"], origem_uf=data["origem"]["uf"], destino_cidade=data["destino"]["cidade"], destino_uf=data["destino"]["uf"], descricao_carga=data["descricaoCarga"], peso_kg=data["pesoKg"], data_coleta=date.fromisoformat(data["dataColeta"]), observacoes=data.get("observacoes"), status=data["status"], criado_em=datetime.fromisoformat(data["criadoEm"]), atualizado_em=datetime.fromisoformat(data["atualizadoEm"])))
                    counts["solicitacoes"] += 1
            db.flush()
            for row in source.execute("SELECT * FROM outbox"):
                if not db.get(OutboxModel, row["solicitacaoId"]):
                    db.add(OutboxModel(id=row["solicitacaoId"], payload=row["payload"], status=row["status"], tentativas=row["tentativas"], proxima_tentativa=row["proximaTentativa"] // 1000, ultimo_erro=row["ultimoErro"]))
            for row in source.execute("SELECT * FROM usuarios"):
                if not db.scalar(select(UserModel).where(UserModel.email == row["email"])):
                    db.add(UserModel(id=row["id"], name=row["nome"], email=row["email"], password_hash=row["senhaHash"], role="ADMIN" if row["papel"] == "ADMIN" else "MEMBER", created_at=datetime.fromisoformat(row["criadoEm"])))
                    counts["usuarios"] += 1
            db.commit()
    finally:
        source.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "create-admin", "import-legacy"])
    parser.add_argument("--source")
    args = parser.parse_args()
    initialize(app.state.engine)
    if args.command == "create-admin":
        from pydantic import TypeAdapter, EmailStr
        email = str(TypeAdapter(EmailStr).validate_python(input("E-mail: ").strip().lower()))
        name = input("Nome: ").strip()
        password = getpass.getpass("Senha (12–128 caracteres): ")
        if not name or not 12 <= len(password) <= 128 or password != getpass.getpass("Confirme: "):
            raise SystemExit("Nome/senha inválidos ou confirmação divergente.")
        with app.state.sessions() as db:
            db.add(UserModel(email=email, name=name, password_hash=hash_password(password), role="ADMIN"))
            db.commit()
        print("Operador criado.")
    elif args.command == "import-legacy":
        if not args.source:
            parser.error("Informe --source apontando para cópia do SQLite anterior.")
        print("Importação idempotente concluída:", import_legacy(args.source, app.state.sessions))
    else:
        print("Schema inicializado.")
