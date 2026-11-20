"""Metadados e exemplos reutilizados entre exportação e documentação em execução."""
import copy
import json
from pathlib import Path


def documented_openapi(app):
    from fastapi.openapi.utils import get_openapi
    spec = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    original = json.loads((Path(__file__).resolve().parents[2] / "docs/openapi.json").read_text(encoding="utf-8"))
    components = spec["components"]["schemas"]
    source = original["components"]["schemas"]
    def resolve(value):
        return resolve(source[value["$ref"].split("/")[-1]]) if "$ref" in value else value
    for name, schema in components.items():
        base = source.get(name, {})
        schema.setdefault("description", base.get("description", f"Contrato reutilizável de {name}."))
        for field, prop in schema.get("properties", {}).items():
            old = resolve(base.get("properties", {}).get(field, {}))
            prop.setdefault("description", old.get("description", f"{field}: atributo do contrato {name}."))
            for key in ("example", "x-apidog-mock"):
                if key in old:
                    prop.setdefault(key, old[key])
            if "examples" in prop:
                prop.setdefault("example", prop["examples"][0])
        if name in ("Cliente", "SolicitacaoOrcamento", "UserResponse", "TokenResponseDTO", "ListaClientes", "ListaSolicitacoes", "Paginacao", "OrcamentoRecebido", "ApiError"):
            schema["required"] = list(schema.get("properties", {}))
    # Exemplos completos, sem credenciais reais ou dados de clientes.
    cid = "c530a965-f481-4d34-a9a6-988be14c0152"
    qid = "87792e48-b293-4a91-a767-4a0d19eeaee6"
    created = "2026-11-20T17:00:00Z"
    contact = {"nome":"Comercial Exemplo Ltda.","email":"compras@example.com","telefone":"+5516991234567","tipoPessoa":"PJ"}
    carga = {"origem":{"cidade":"Ribeirão Preto","uf":"SP"},"destino":{"cidade":"Campinas","uf":"SP"},"descricaoCarga":"20 caixas de peças automotivas embaladas.","pesoKg":350.5,"dataColeta":"2026-12-10","observacoes":"Coleta em horário comercial."}
    person = {**contact,"id":cid,"criadoEm":created,"atualizadoEm":created}
    order = {**carga,"clienteId":cid,"id":qid,"status":"RECEBIDA","statusEmail":"PENDENTE","criadoEm":created,"atualizadoEm":created}
    pagination = {"pagina":1,"limite":20,"total":1,"totalPaginas":1}
    user = {"id":cid,"name":"Operador de exemplo","email":"operador@example.com","role":"ADMIN"}
    examples = {"Localidade":carga["origem"],"CreateClienteDTO":contact,"UpdateClienteDTO":{"nome":"Contato atualizado"},"Cliente":person,"CreateSolicitacaoDTO":{**carga,"clienteId":cid},"UpdateSolicitacaoDTO":{"status":"EM_ANALISE"},"SolicitacaoOrcamento":order,"Paginacao":pagination,"ListaClientes":{"dados":[person],"paginacao":pagination},"ListaSolicitacoes":{"dados":[order],"paginacao":pagination},"OrcamentoPublicoDTO":{**carga,"cliente":contact},"OrcamentoRecebido":{"id":qid,"status":"RECEBIDA","statusEmail":"PENDENTE","mensagem":"Solicitação registrada."},"LoginRequestDTO":{"email":"operador@example.com","password":"Exemplo-sem-validade-2026"},"UserResponse":user,"TokenResponseDTO":{"accessToken":"JWT_EXEMPLO_SEM_VALIDADE","tokenType":"bearer","expiresIn":3600,"user":user},"InvalidParam":{"name":"nome","reason":"Informe ao menos dois caracteres."},"ApiError":{"type":"https://donitransportes.com.br/problems/validation-error","title":"Dados inválidos","status":422,"detail":"Confira os campos informados.","instance":"/api/v1/clientes","invalidParams":[{"name":"nome","reason":"Informe ao menos dois caracteres."}]}}
    for name, example in examples.items():
        if name not in components:
            continue
        components[name]["example"] = example
        for field, value in example.items():
            if field in components[name].get("properties", {}):
                components[name]["properties"][field].setdefault("example", value)
    for name, schema in components.items():
        for field, prop in schema.get("properties", {}).items():
            if prop.get("format") == "uuid":
                prop.setdefault("x-apidog-mock", "{{$string.uuid}}")
                prop.setdefault("example", cid)
            elif prop.get("format") == "date-time":
                prop.setdefault("x-apidog-mock", "{{$date.isoTimestamp}}")
                prop.setdefault("example", created)
    for item in spec["paths"].values():
        for method, operation in item.items():
            if method not in ("get", "post", "patch", "delete"):
                continue
            for code, response in operation.get("responses", {}).items():
                if code == "204":
                    response.pop("content", None)
                elif int(code) >= 400:
                    response["content"] = {"application/problem+json":{"schema":{"$ref":"#/components/schemas/ApiError"}}}
            if method == "post" and "201" in operation["responses"]:
                operation["responses"]["201"]["headers"] = {"Location":{"description":"URI relativa do recurso criado.","schema":{"type":"string"},"example":"/api/v1/solicitacoes-orcamento/" + qid}}
            for media in list(operation.get("requestBody", {}).get("content", {}).values()) + [m for r in operation.get("responses", {}).values() for m in r.get("content", {}).values()]:
                ref = media.get("schema", {}).get("$ref", "").split("/")[-1]
                if ref in examples:
                    media["example"] = copy.deepcopy(examples[ref])
    spec["servers"] = [{"url":"https://donitransportes.com.br","description":"Site e proxy de produção"},{"url":"http://127.0.0.1:8000","description":"Execução local"}]
    return spec
