from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from src.api.main import create_app
from src.api.models import UserModel
from src.api.security import hash_password, make_token


class FakeMail:
    ready = True
    def __init__(self):
        self.messages = []
        self.fail = False
    def send(self, snapshot):
        if self.fail:
            raise RuntimeError("simulated failure")
        self.messages.append(snapshot)


@pytest.fixture
def app(tmp_path):
    return create_app(f"sqlite:///{tmp_path / 'test.sqlite'}", "test-only-secret-with-at-least-32-characters", FakeMail(), scheduler=False)


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def accounts(client, app):
    accounts = {}
    with app.state.sessions() as db:
        for role in ("ADMIN", "MEMBER"):
            user = UserModel(id=str(uuid4()), name="Operador de teste", email=f"{role.lower()}@example.com", password_hash=hash_password("Teste-seguro-2026"), role=role)
            db.add(user)
            db.flush()
            accounts[role] = {"user": user, "headers": {"Authorization": "Bearer " + make_token(user, app.state.jwt_secret)}}
        db.commit()
    return accounts


@pytest.fixture
def contact():
    return {"nome": "Cliente de teste", "email": "cliente@example.com", "telefone": "+5516991234567", "tipoPessoa": "PF"}


@pytest.fixture
def cargo():
    return {"origem": {"cidade": "Ribeirão Preto", "uf": "SP"}, "destino": {"cidade": "Campinas", "uf": "SP"}, "descricaoCarga": "Caixas de peças embaladas para transporte.", "pesoKg": 350.5, "dataColeta": "2026-12-10", "observacoes": None}
