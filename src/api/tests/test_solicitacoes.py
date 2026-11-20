from sqlalchemy import func, select, update
from src.api.models import ClienteModel, SolicitacaoModel, OutboxModel
from src.api.notifications import flush, message_fields


def test_quote_crud_and_immutable_contact(client, accounts, contact, cargo):
    headers = accounts["ADMIN"]["headers"]
    cid = client.post("/api/v1/clientes", json=contact, headers=headers).json()["id"]
    r = client.post("/api/v1/solicitacoes-orcamento", json={**cargo, "clienteId": cid}, headers=headers)
    assert r.status_code == 201 and r.headers["location"].endswith(r.json()["id"])
    path = r.headers["location"]
    assert client.get(path, headers=headers).json()["statusEmail"] == "ENVIADO"
    assert client.patch(path, json={"status": "COTADA", "observacoes": "Coleta confirmada"}, headers=headers).status_code == 200
    assert client.patch(path, json={"observacoes": None}, headers=headers).json()["observacoes"] is None
    assert client.patch(path, json={"clienteId": cid}, headers=headers).status_code == 422
    assert client.get("/api/v1/solicitacoes-orcamento?status=COTADA&clienteId=" + cid, headers=headers).json()["paginacao"]["total"] == 1
    assert client.delete(path, headers=accounts["MEMBER"]["headers"]).status_code == 403
    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404


def test_public_quote_is_atomic_and_notification_has_contacts(client, app, contact, cargo, accounts):
    r = client.post("/api/v1/orcamentos/publico", json={**cargo, "cliente": contact})
    assert r.status_code == 201
    assert "email" not in r.json() and "cliente" not in r.json()
    assert len(app.state.mail.messages) == 1
    fields = message_fields(app.state.mail.messages[0])
    assert fields["email"] == contact["email"] and fields["Contato pelo WhatsApp"].startswith("https://wa.me/5516991234567")
    assert client.get("/api/v1/clientes").status_code == 401
    assert client.patch(r.headers["location"], json={"status": "EM_ANALISE"}, headers=accounts["ADMIN"]["headers"]).status_code == 200
    assert len(app.state.mail.messages) == 1


def test_smtp_failure_retries_without_second_quote(client, app, contact, cargo):
    app.state.mail.fail = True
    r = client.post("/api/v1/orcamentos/publico", json={**cargo, "cliente": contact})
    assert r.status_code == 201
    with app.state.sessions() as db:
        row = db.get(OutboxModel, r.json()["id"])
        assert row.status == "FALHOU" and row.tentativas == 1
        db.execute(update(OutboxModel).values(proxima_tentativa=0))
        db.commit()
    app.state.mail.fail = False
    flush(app.state.sessions, app.state.mail)
    flush(app.state.sessions, app.state.mail)
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(SolicitacaoModel)) == 1
        assert db.get(OutboxModel, r.json()["id"]).status == "ENVIADO"
    assert len(app.state.mail.messages) == 1


def test_outbox_failure_rolls_back_everything(client, app, monkeypatch, contact, cargo):
    from src.api.routers import solicitacoes
    def fail(*args):
        raise RuntimeError("simulate database failure")
    monkeypatch.setattr(solicitacoes, "enqueue", fail)
    assert client.post("/api/v1/orcamentos/publico", json={**cargo, "cliente": contact}).status_code == 500
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ClienteModel)) == 0
        assert db.scalar(select(func.count()).select_from(SolicitacaoModel)) == 0


def test_unconfigured_email_does_not_claim_success(client, app, contact, cargo):
    app.state.mail.ready = False
    assert client.post("/api/v1/orcamentos/publico", json={**cargo, "cliente": contact}).status_code == 503


def test_nonexistent_contact(client, accounts, cargo):
    r = client.post("/api/v1/solicitacoes-orcamento", json={**cargo, "clienteId": "00000000-0000-0000-0000-000000000000"}, headers=accounts["ADMIN"]["headers"])
    assert r.status_code == 422 and r.json()["invalidParams"][0]["name"] == "clienteId"
