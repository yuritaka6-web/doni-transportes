from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..exceptions import ApiFailure
from ..models import ClienteModel, SolicitacaoModel, utcnow
from ..schemas import Cliente, CreateClienteDTO, UpdateClienteDTO, ListaClientes, ListaSolicitacoes
from ..security import get_current_user, require_roles
from ..views import cliente_view, contact_values, quote_view

router = APIRouter(prefix="/api/v1/clientes", tags=["Clientes"])


def find(db, identifier):
    row = db.get(ClienteModel, str(identifier))
    if row is None:
        raise ApiFailure(404, "Cliente não encontrado.")
    return row


@router.post("", response_model=Cliente, status_code=201, dependencies=[Depends(require_roles("ADMIN", "MEMBER"))], summary="Cadastrar cliente")
def create(data: CreateClienteDTO, response: Response, db=Depends(get_db)):
    row = ClienteModel(**contact_values(data))
    db.add(row)
    db.commit()
    db.refresh(row)
    response.headers["Location"] = f"/api/v1/clientes/{row.id}"
    return cliente_view(row)


@router.get("", response_model=ListaClientes, dependencies=[Depends(get_current_user)], summary="Listar clientes")
def listing(pagina: int = Query(1, ge=1, le=1000000), limite: int = Query(20, ge=1, le=100), busca: str | None = Query(None, min_length=1, max_length=120), db=Depends(get_db)):
    filters = [func.lower(ClienteModel.nome).contains(busca.lower(), autoescape=True)] if busca else []
    total = db.scalar(select(func.count()).select_from(ClienteModel).where(*filters))
    rows = db.scalars(select(ClienteModel).where(*filters).order_by(ClienteModel.criado_em.desc(), ClienteModel.id).offset((pagina - 1) * limite).limit(limite)).all()
    return {"dados": [cliente_view(row) for row in rows], "paginacao": {"pagina": pagina, "limite": limite, "total": total, "totalPaginas": (total + limite - 1) // limite}}


@router.get("/{id}/solicitacoes-orcamento", response_model=ListaSolicitacoes, dependencies=[Depends(get_current_user)], summary="Consultar relacionamento cliente e solicitações")
def relationship(id: UUID, pagina: int = Query(1, ge=1, le=1000000), limite: int = Query(20, ge=1, le=100), db=Depends(get_db)):
    # Carregar somente os pedidos da página; eager loading mantém número fixo de consultas.
    ids = select(SolicitacaoModel.id).where(SolicitacaoModel.cliente_id == str(id)).order_by(SolicitacaoModel.criado_em.desc(), SolicitacaoModel.id).offset((pagina - 1) * limite).limit(limite)
    row = db.scalar(select(ClienteModel).where(ClienteModel.id == str(id)).options(selectinload(ClienteModel.solicitacoes.and_(SolicitacaoModel.id.in_(ids))).selectinload(SolicitacaoModel.notificacao)))
    if row is None:
        raise ApiFailure(404, "Cliente não encontrado.")
    data = [quote_view(order) for order in row.solicitacoes]
    total = db.scalar(select(func.count()).select_from(SolicitacaoModel).where(SolicitacaoModel.cliente_id == str(id)))
    return {"dados": data, "paginacao": {"pagina": pagina, "limite": limite, "total": total, "totalPaginas": (total + limite - 1) // limite}}


@router.get("/{id}", response_model=Cliente, dependencies=[Depends(get_current_user)], summary="Buscar cliente")
def item(id: UUID, db=Depends(get_db)):
    return cliente_view(find(db, id))


@router.patch("/{id}", response_model=Cliente, dependencies=[Depends(require_roles("ADMIN", "MEMBER"))], summary="Atualizar cliente")
def patch(id: UUID, data: UpdateClienteDTO, db=Depends(get_db)):
    row = find(db, id)
    for key, value in contact_values(data).items():
        setattr(row, key, value)
    row.atualizado_em = utcnow()
    db.commit()
    return cliente_view(row)


@router.delete("/{id}", status_code=204, dependencies=[Depends(require_roles("ADMIN"))], summary="Excluir cliente")
def delete(id: UUID, db=Depends(get_db)):
    row = find(db, id)
    if db.scalar(select(SolicitacaoModel.id).where(SolicitacaoModel.cliente_id == str(id)).limit(1)):
        raise ApiFailure(409, "Cliente possui solicitações vinculadas.")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
