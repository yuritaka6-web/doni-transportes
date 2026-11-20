import pytest


@pytest.mark.parametrize("patch", [{}, {"nome": None}, {"nome": " "}, {"email": "invalid"}, {"telefone": "123"}, {"tipoPessoa": "OUTRO"}, {"extra": "field"}])
def test_invalid_patch(client, accounts, contact, patch):
    headers = accounts["ADMIN"]["headers"]
    path = client.post("/api/v1/clientes", json=contact, headers=headers).headers["location"]
    r = client.patch(path, json=patch, headers=headers)
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert {"type", "title", "status", "detail", "instance", "invalidParams"} == set(r.json())


def test_malformed_json_query_origin_and_private_files(client, accounts):
    h = {**accounts["ADMIN"]["headers"], "Content-Type": "application/json"}
    assert client.post("/api/v1/clientes", content="{", headers=h).status_code == 400
    assert client.get("/api/v1/clientes?pagina=0", headers=h).status_code == 400
    assert client.get("/api/v1/clientes?pagina=1&pagina=2", headers=h).status_code == 400
    assert client.get("/api/v1/clientes?foo=bar", headers=h).status_code == 400
    assert client.get("/api/v1/clientes/not-a-uuid", headers=h).status_code == 400
    assert client.post("/api/v1/clientes", json={}, headers={**h, "Origin": "https://untrusted.example"}).status_code == 403
    assert client.post("/api/v1/clientes", content="x", headers={**accounts["ADMIN"]["headers"], "Content-Type": "text/plain"}).status_code == 415
    assert client.post("/api/v1/clientes", content="x" * 65537, headers=h).status_code == 413
    for path in ("/.env", "/data/doni-v2.sqlite", "/server.mjs", "/src/api/main.py"):
        assert client.get(path).status_code == 404
