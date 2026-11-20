from sqlalchemy import event


def test_contact_crud_filters_and_not_found(client, accounts, contact):
    headers = accounts["ADMIN"]["headers"]
    created = client.post("/api/v1/clientes", json=contact, headers=headers)
    assert created.status_code == 201
    path = created.headers["location"]
    assert client.get(path, headers=headers).json()["nome"] == contact["nome"]
    assert client.get("/api/v1/clientes?busca=TESTE&pagina=1&limite=1", headers=headers).json()["paginacao"]["total"] == 1
    assert client.get("/api/v1/clientes?busca=%25", headers=headers).json()["paginacao"]["total"] == 0
    assert client.patch(path, json={"tipoPessoa": "PJ"}, headers=headers).json()["tipoPessoa"] == "PJ"
    removed = client.delete(path, headers=headers)
    assert removed.status_code == 204 and removed.content == b""
    assert client.get(path, headers=headers).status_code == 404
    assert client.delete(path, headers=headers).status_code == 404


def test_relationship_and_restrict_delete(client, app, accounts, contact, cargo):
    headers = accounts["ADMIN"]["headers"]
    contact_id = client.post("/api/v1/clientes", json=contact, headers=headers).json()["id"]
    for _ in range(3):
        assert client.post("/api/v1/solicitacoes-orcamento", json={**cargo, "clienteId": contact_id}, headers=headers).status_code == 201
    queries = []
    def track(*args):
        queries.append(args[2])
    event.listen(app.state.engine, "before_cursor_execute", track)
    try:
        r = client.get(f"/api/v1/clientes/{contact_id}/solicitacoes-orcamento", headers=headers)
    finally:
        event.remove(app.state.engine, "before_cursor_execute", track)
    assert r.status_code == 200 and len(r.json()["dados"]) == 3
    assert len(queries) <= 5  # autenticação + cliente + lote de pedidos + lote da outbox
    assert client.delete(f"/api/v1/clientes/{contact_id}", headers=headers).status_code == 409
