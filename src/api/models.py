"""Modelo relacional normalizado; sem documentos JSON no lugar das entidades."""
from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow():
    return datetime.now(timezone.utc)


def identifier():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default="MEMBER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ClienteModel(Base):
    __tablename__ = "contacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(254))
    telefone: Mapped[str] = mapped_column(String(14))
    tipo_pessoa: Mapped[str] = mapped_column(String(2), default="PF")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    solicitacoes: Mapped[list["SolicitacaoModel"]] = relationship(back_populates="cliente", passive_deletes="all")


class SolicitacaoModel(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("contacts.id", ondelete="RESTRICT"), index=True)
    origem_cidade: Mapped[str] = mapped_column(String(100))
    origem_uf: Mapped[str] = mapped_column(String(2))
    destino_cidade: Mapped[str] = mapped_column(String(100))
    destino_uf: Mapped[str] = mapped_column(String(2))
    descricao_carga: Mapped[str] = mapped_column(Text)
    peso_kg: Mapped[float] = mapped_column(Float)
    data_coleta: Mapped[date] = mapped_column(Date)
    observacoes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="RECEBIDA", index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cliente: Mapped[ClienteModel] = relationship(back_populates="solicitacoes")
    notificacao: Mapped["OutboxModel | None"] = relationship(back_populates="solicitacao", cascade="all, delete-orphan", uselist=False)


class OutboxModel(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), primary_key=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="PENDENTE")
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    proxima_tentativa: Mapped[int] = mapped_column(Integer, default=0, index=True)
    ultimo_erro: Mapped[str | None] = mapped_column(String(80), nullable=True)
    solicitacao: Mapped[SolicitacaoModel] = relationship(back_populates="notificacao")


class RateLimitModel(Base):
    __tablename__ = "request_limits"
    chave: Mapped[str] = mapped_column(String(160), primary_key=True)
    quantidade: Mapped[int] = mapped_column(Integer, default=1)
    expira_em: Mapped[int] = mapped_column(Integer, index=True)


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

Index("ix_quotes_created_id", SolicitacaoModel.criado_em, SolicitacaoModel.id)
