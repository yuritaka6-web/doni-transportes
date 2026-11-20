import os
import json
from fastapi import Request
from pathlib import Path
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from .models import Base, SchemaVersion, UserModel


def create_database(url: str | None = None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///./data/doni-v2.sqlite")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("sqlite:///./"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}, pool_pre_ping=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def pragmas(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
    return engine, sessionmaker(engine, expire_on_commit=False)


def initialize(engine):
    # Versão 1 é aditiva: as tabelas do backend anterior nunca são removidas.
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.get(SchemaVersion, 1):
            session.add(SchemaVersion(version=1))
            session.commit()
        for user in json.loads(os.getenv("BOOTSTRAP_USERS_JSON", "[]")):
            if not session.scalar(select(UserModel).where(UserModel.email == user["email"])):
                session.add(UserModel(id=user["id"], name=user["name"], email=user["email"], password_hash=user["password_hash"], role=user["role"]))
        session.commit()


def get_db(request: Request):
    with request.app.state.sessions() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
