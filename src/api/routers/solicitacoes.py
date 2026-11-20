from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..exceptions import ApiFailure
from ..models import ClienteModel, SolicitacaoModel, utcnow
from ..notifications import enqueue, flush
from ..schemas import CreateSolicitacaoDTO, UpdateSolicitacaoDTO, SolicitacaoOrcamento, ListaSolicitacoes, StatusSolicitacao, OrcamentoPublicoDTO, OrcamentoRecebido
from ..security import enforce_limit, get_current_user, require_roles
from ..views import cliente_view, contact_values, quote_values, quote_view

router = APIRouter(prefix="/api/v1", tags=["Solicitações de orçamento"])


def find(db, identifier):
    row = db.scalar(select(SolicitacaoModel).where(SolicitacaoModel.id == str(identifier)).options(selectinload(SolicitacaoModel.notificacao)))
    if row is None:
        raise ApiFailure(404, "Solicitação não encontrada.")
    return row


def register(db, data, client):
    row = SolicitacaoModel(**quote_values(data))
    db.add(row)
    db.flush()
    view = quote_view(row)
    enqueue(db, jsonable_encoder(cliente_view(client)), jsonable_encoder(view))
    db.flush()
    return row


@router.post("/solicitacoes-orcamento", response_model=SolicitacaoOrcamento, status_code=201, dependencies=[Depends(require_roles("ADMIN", "MEMBER"))], summary="Criar solicitação de orçamento")
def create(data: CreateSolicitacaoDTO, response: Response, request: Request, background: BackgroundTasks, db=Depends(get_db)):
    client = db.get(ClienteModel, str(data.clienteId))
    if client is None:
        raise ApiFailure(422, "Cliente vinculado não existe.", [{"name": "clienteId", "reason": "Cadastre o cliente antes da solicitação."}])
    row = register(db, data, client)
    db.commit()
    db.expire(row, ["notificacao"])
    response.headers["Location"] = f"/api/v1/solicitacoes-orcamento/{row.id}"
    background.add_task(flush, request.app.state.sessions, request.app.state.mail)
    return quote_view(row)


@router.get("/solicitacoes-orcamento", response_model=ListaSolicitacoes, dependencies=[Depends(get_current_user)], summary="Listar solicitações de orçamento")
def listing(pagina: int = Query(1, ge=1, le=1000000), limite: int = Query(20, ge=1, le=100), status: StatusSolicitacao | None = None, clienteId: UUID | None = None, db=Depends(get_db)):
    filters = []
    if status:
        filters.append(SolicitacaoModel.status == status)
    if clienteId:
        filters.append(SolicitacaoModel.cliente_id == str(clienteId))
    total = db.scalar(select(func.count()).select_from(SolicitacaoModel).where(*filters))
    rows = db.scalars(select(SolicitacaoModel).where(*filters).options(selectinload(SolicitacaoModel.notificacao)).order_by(SolicitacaoModel.criado_em.desc(), SolicitacaoModel.id).offset((pagina - 1) * limite).limit(limite)).all()
    return {"dados": [quote_view(row) for row in rows], "paginacao": {"pagina": pagina, "limite": limite, "total": total, "totalPaginas": (total + limite - 1) // limite}}


@router.get("/solicitacoes-orcamento/{id}", response_model=SolicitacaoOrcamento, dependencies=[Depends(get_current_user)], summary="Buscar solicitação de orçamento")
def item(id: UUID, db=Depends(get_db)):
    return quote_view(find(db, id))


@router.patch("/solicitacoes-orcamento/{id}", response_model=SolicitacaoOrcamento, dependencies=[Depends(require_roles("ADMIN", "MEMBER"))], summary="Atualizar solicitação de orçamento")
def patch(id: UUID, data: UpdateSolicitacaoDTO, db=Depends(get_db)):
    row = find(db, id)
    for key, value in quote_values(data).items():
        setattr(row, key, value)
    row.atualizado_em = utcnow()
    db.commit()
    return quote_view(row)


@router.delete("/solicitacoes-orcamento/{id}", status_code=204, dependencies=[Depends(require_roles("ADMIN"))], summary="Excluir solicitação de orçamento")
def delete(id: UUID, db=Depends(get_db)):
    db.delete(find(db, id))
    db.commit()
    return Response(status_code=204)


@router.post("/orcamentos/publico", response_model=OrcamentoRecebido, status_code=201, tags=["Formulário público"], summary="Enviar orçamento pelo site")
def public(data: OrcamentoPublicoDTO, request: Request, response: Response, background: BackgroundTasks, db=Depends(get_db)):
    enforce_limit(request, db, "orcamento", 10, 600)
    if not request.app.state.mail.ready:
        raise ApiFailure(503, "O serviço de orçamento está em configuração. Entre em contato com a empresa.")
    client = ClienteModel(**contact_values(data.cliente))
    db.add(client)
    db.flush()
    fields = data.model_dump(exclude={"cliente"})
    order = register(db, CreateSolicitacaoDTO(**fields, clienteId=client.id), client)
    db.commit()
    response.headers["Location"] = f"/api/v1/solicitacoes-orcamento/{order.id}"
    background.add_task(flush, request.app.state.sessions, request.app.state.mail)
    return {"id": order.id, "status": "RECEBIDA", "statusEmail": "PENDENTE", "mensagem": "Solicitação registrada. A equipe poderá entrar em contato por e-mail ou WhatsApp."}
