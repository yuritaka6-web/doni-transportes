from .models import ClienteModel, SolicitacaoModel
from datetime import timezone


def utc(value):
    # SQLite não preserva o offset de DateTime; o domínio armazena sempre UTC.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def cliente_view(row):
    return {"id": row.id, "nome": row.nome, "email": row.email, "telefone": row.telefone, "tipoPessoa": row.tipo_pessoa, "criadoEm": utc(row.criado_em), "atualizadoEm": utc(row.atualizado_em)}


def quote_view(row):
    return {"id": row.id, "clienteId": row.cliente_id, "origem": {"cidade": row.origem_cidade, "uf": row.origem_uf}, "destino": {"cidade": row.destino_cidade, "uf": row.destino_uf}, "descricaoCarga": row.descricao_carga, "pesoKg": row.peso_kg, "dataColeta": row.data_coleta, "observacoes": row.observacoes, "status": row.status, "statusEmail": row.notificacao.status if row.notificacao else "PENDENTE", "criadoEm": utc(row.criado_em), "atualizadoEm": utc(row.atualizado_em)}


def user_view(row):
    return {"id": row.id, "name": row.name, "email": row.email, "role": row.role}


def contact_values(data):
    values = data.model_dump(exclude_unset=True)
    if "tipoPessoa" in values:
        values["tipo_pessoa"] = values.pop("tipoPessoa")
    return values


def quote_values(data):
    values = data.model_dump(exclude_unset=True)
    for name in ("origem", "destino"):
        if name in values:
            location = values.pop(name)
            values[name + "_cidade"], values[name + "_uf"] = location["cidade"], location["uf"]
    for camel, snake in {"clienteId": "cliente_id", "descricaoCarga": "descricao_carga", "pesoKg": "peso_kg", "dataColeta": "data_coleta"}.items():
        if camel in values:
            values[snake] = str(values.pop(camel)) if camel == "clienteId" else values.pop(camel)
    return values
