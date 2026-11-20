import json
import sqlite3
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from src.api.main import create_app
from src.api.models import ClienteModel, SchemaVersion
from src.api.security import hash_password
from scripts.manage import import_legacy


def test_restart_persists_data_and_schema_is_idempotent(tmp_path, contact):
    url = f"sqlite:///{tmp_path / 'persistent.sqlite'}"
    one = create_app(url, "test-secret-with-at-least-32-characters", scheduler=False)
    with TestClient(one):
        with one.state.sessions() as db:
            db.add(ClienteModel(nome=contact["nome"], email=contact["email"], telefone=contact["telefone"]))
            db.commit()
    two = create_app(url, "test-secret-with-at-least-32-characters", scheduler=False)
    with TestClient(two):
        with two.state.sessions() as db:
            assert db.scalar(select(func.count()).select_from(ClienteModel)) == 1
            assert db.scalar(select(func.count()).select_from(SchemaVersion)) == 1


def test_import_legacy_preserves_hash_ids_and_is_idempotent(tmp_path, client, app, contact):
    file = tmp_path / "legacy.sqlite"
    cid, uid = str(uuid4()), str(uuid4())
    stamp = "2026-11-20T17:00:00Z"
    with sqlite3.connect(file) as db:
        db.executescript("CREATE TABLE clientes(id TEXT,dados TEXT);CREATE TABLE solicitacoes(id TEXT,clienteId TEXT,dados TEXT);CREATE TABLE outbox(solicitacaoId TEXT,payload TEXT,status TEXT,tentativas INTEGER,proximaTentativa INTEGER,ultimoErro TEXT);CREATE TABLE usuarios(id TEXT,nome TEXT,email TEXT,senhaHash TEXT,papel TEXT,criadoEm TEXT);")
        db.execute("INSERT INTO clientes VALUES (?,?)", (cid, json.dumps({**contact,"id":cid,"criadoEm":stamp,"atualizadoEm":stamp})))
        db.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?)", (uid,"Autor","autor@example.com",hash_password("Senha-legada-2026"),"ADMIN",stamp))
    assert import_legacy(file, app.state.sessions)["usuarios"] == 1
    assert import_legacy(file, app.state.sessions) == {"clientes":0,"solicitacoes":0,"usuarios":0}
    login = client.post("/api/v1/auth/login", json={"email":"autor@example.com","password":"Senha-legada-2026"})
    assert login.status_code == 200 and login.json()["user"]["id"] == uid
    r = client.get(f"/api/v1/clientes/{cid}", headers={"Authorization":"Bearer " + login.json()["accessToken"]})
    assert r.status_code == 200 and r.json()["email"] == contact["email"]


def test_site_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/logo-doni-transparente.png").headers["content-type"] == "image/png"
    assert client.get("/health").json()["version"] == "2.0.0"
