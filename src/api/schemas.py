"""Contratos Pydantic v2 extraídos dos componentes do domínio."""
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, from_attributes=True)


class TipoPessoa(StrEnum):
    PF = "PF"
    PJ = "PJ"


class Papel(StrEnum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class StatusSolicitacao(StrEnum):
    RECEBIDA = "RECEBIDA"
    EM_ANALISE = "EM_ANALISE"
    COTADA = "COTADA"
    CANCELADA = "CANCELADA"


class StatusEmail(StrEnum):
    PENDENTE = "PENDENTE"
    ENVIADO = "ENVIADO"
    FALHOU = "FALHOU"


class UF(StrEnum):
    AC="AC"; AL="AL"; AP="AP"; AM="AM"; BA="BA"; CE="CE"; DF="DF"; ES="ES"; GO="GO"
    MA="MA"; MT="MT"; MS="MS"; MG="MG"; PA="PA"; PB="PB"; PR="PR"; PE="PE"; PI="PI"
    RJ="RJ"; RN="RN"; RS="RS"; RO="RO"; RR="RR"; SC="SC"; SP="SP"; SE="SE"; TO="TO"


Nome = Annotated[str, Field(min_length=2, max_length=120, pattern=r"\S", description="Nome do contato ou razão social.", examples=["Comercial Exemplo Ltda."])]
Telefone = Annotated[str, Field(min_length=13, max_length=14, pattern=r"^\+55[1-9][0-9][0-9]{8,9}$", description="WhatsApp brasileiro com código de país e DDD.", examples=["+5516991234567"])]
Email = Annotated[EmailStr, Field(max_length=254, description="E-mail para contato e Reply-To.", examples=["compras@example.com"])]
Carga = Annotated[str, Field(min_length=10, max_length=2000, pattern=r"\S", description="Conteúdo, embalagem e cuidados com a carga.", examples=["20 caixas de peças automotivas embaladas."])]
Peso = Annotated[float, Field(ge=0.01, le=30000, strict=True, allow_inf_nan=False, description="Peso estimado em quilogramas.", examples=[350.5])]


class Localidade(Contract):
    cidade: str = Field(min_length=2, max_length=100, pattern=r"\S", description="Cidade da coleta ou entrega.", examples=["Ribeirão Preto"])
    uf: UF = Field(description="Unidade federativa brasileira.", examples=["SP"])


class CreateClienteDTO(Contract):
    nome: Nome
    email: Email
    telefone: Telefone
    tipoPessoa: TipoPessoa = Field(default=TipoPessoa.PF, description="Pessoa física ou jurídica.", examples=["PF"])


class Cliente(CreateClienteDTO):
    id: UUID = Field(description="Identificador atribuído pelo servidor.")
    criadoEm: datetime = Field(description="Data de criação em UTC.")
    atualizadoEm: datetime = Field(description="Última alteração em UTC.")


class Partial(Contract):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        schema = super().__get_pydantic_json_schema__(core_schema, handler)
        schema["minProperties"] = 1
        for name, prop in schema.get("properties", {}).items():
            if name != "observacoes" and "anyOf" in prop:
                choices = [p for p in prop["anyOf"] if p.get("type") != "null"]
                if len(choices) == 1:
                    prop.pop("anyOf")
                    prop.pop("default", None)
                    prop.update(choices[0])
        return schema

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo.")
        for name in self.model_fields_set:
            if name != "observacoes" and getattr(self, name) is None:
                raise ValueError(f"O campo {name} não aceita null.")
        return self


class UpdateClienteDTO(Partial):
    nome: Nome | None = None
    email: Email | None = None
    telefone: Telefone | None = None
    tipoPessoa: TipoPessoa | None = None


class DadosCarga(Contract):
    origem: Localidade = Field(description="Cidade e UF da coleta.")
    destino: Localidade = Field(description="Cidade e UF da entrega.")
    descricaoCarga: Carga
    pesoKg: Peso
    dataColeta: date = Field(description="Data desejada, sujeita à confirmação.", examples=["2026-12-10"])
    observacoes: str | None = Field(default=None, max_length=1000, description="Instruções adicionais; null indica ausência.", examples=["Coleta em horário comercial."])


class CreateSolicitacaoDTO(DadosCarga):
    clienteId: UUID = Field(description="Identificador do cliente existente.")


class UpdateSolicitacaoDTO(Partial):
    origem: Localidade | None = None
    destino: Localidade | None = None
    descricaoCarga: Carga | None = None
    pesoKg: Peso | None = None
    dataColeta: date | None = None
    observacoes: str | None = Field(default=None, max_length=1000)
    status: StatusSolicitacao | None = None


class SolicitacaoOrcamento(CreateSolicitacaoDTO):
    id: UUID = Field(description="Protocolo da solicitação.")
    status: StatusSolicitacao = Field(description="Situação comercial.")
    statusEmail: StatusEmail = Field(description="Situação do envio da notificação, sem garantir leitura.")
    criadoEm: datetime = Field(description="Criação em UTC.")
    atualizadoEm: datetime = Field(description="Última alteração em UTC.")


class OrcamentoPublicoDTO(DadosCarga):
    cliente: CreateClienteDTO = Field(description="Dados do contato que solicita o orçamento.")


class OrcamentoRecebido(Contract):
    id: UUID = Field(description="Protocolo para acompanhamento com a empresa.")
    status: StatusSolicitacao = StatusSolicitacao.RECEBIDA
    statusEmail: StatusEmail = StatusEmail.PENDENTE
    mensagem: str = Field(description="Confirmação do registro, sem prometer entrega de e-mail.")


class Paginacao(Contract):
    pagina: int = Field(ge=1, le=1000000)
    limite: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    totalPaginas: int = Field(ge=0)


class ListaClientes(Contract):
    dados: list[Cliente]
    paginacao: Paginacao


class ListaSolicitacoes(Contract):
    dados: list[SolicitacaoOrcamento]
    paginacao: Paginacao


class LoginRequestDTO(Contract):
    email: Email
    password: str = Field(min_length=6, max_length=256, description="Senha do operador; nunca devolvida em respostas.", json_schema_extra={"writeOnly": True})


class UserResponse(Contract):
    id: UUID
    name: str
    email: Email
    role: Papel


class TokenResponseDTO(Contract):
    accessToken: str = Field(description="JWT assinado HS256 com duração limitada.")
    tokenType: str = "bearer"
    expiresIn: int = Field(default=3600, ge=1)
    user: UserResponse


class InvalidParam(Contract):
    name: str
    reason: str


class ApiError(Contract):
    type: str = Field(description="URI identificadora do tipo de problema.", json_schema_extra={"format": "uri"})
    title: str
    status: int = Field(ge=400, le=599)
    detail: str
    instance: str
    invalidParams: list[InvalidParam] = Field(default_factory=list)
