import jwt
from src.api.security import make_token, verify_password, hash_password


def test_login_and_me(client, accounts):
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Teste-seguro-2026"})
    assert r.status_code == 200
    data = r.json()
    assert data["tokenType"] == "bearer" and data["expiresIn"] == 3600
    claims = jwt.decode(data["accessToken"], options={"verify_signature": False})
    assert {"sub", "email", "role", "iat", "exp", "jti", "iss", "aud"} <= claims.keys()
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + data["accessToken"]}).json()["role"] == "ADMIN"
    assert "password" not in str(data["user"]).lower()


def test_invalid_missing_expired_and_wrong_signature(client, app, accounts):
    user = accounts["ADMIN"]["user"]
    for token in (None, "invalid", make_token(user, app.state.jwt_secret, -10), make_token(user, "wrong-key-with-at-least-32-characters")):
        r = client.get("/api/v1/clientes", headers={"Authorization": "Bearer " + token} if token else {})
        assert r.status_code == 401
        assert r.headers["www-authenticate"] == "Bearer"
        assert r.json()["type"].endswith("unauthorized")


def test_bad_login_rate_limit(client, accounts):
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "incorreta"}).status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "incorreta"})
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0


def test_password_hash():
    one, two = hash_password("Senha-segura-2026"), hash_password("Senha-segura-2026")
    assert one != two and verify_password("Senha-segura-2026", one)
    assert not verify_password("incorreta", one)
    assert not verify_password("x", "invalid")


def test_member_can_write_but_not_delete(client, accounts, contact):
    member = accounts["MEMBER"]["headers"]
    created = client.post("/api/v1/clientes", json=contact, headers=member)
    assert created.status_code == 201
    path = created.headers["location"]
    assert client.patch(path, json={"nome": "Contato atualizado"}, headers=member).status_code == 200
    assert client.delete(path, headers=member).status_code == 403
    assert client.delete(path, headers=accounts["ADMIN"]["headers"]).status_code == 204
