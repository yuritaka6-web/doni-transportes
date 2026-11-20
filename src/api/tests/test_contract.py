import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker


def test_contract_components_examples_and_security(client, app):
    spec = app.openapi()
    count = 0
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            count += 1
            contents = list(operation.get("requestBody", {}).get("content", {}).values())
            for code, response in operation["responses"].items():
                if code == "204":
                    assert "content" not in response
                contents += list(response.get("content", {}).values())
            for media in contents:
                assert "$ref" in media["schema"]
                if "example" in media:
                    Draft202012Validator({**media["schema"], "components": spec["components"]}, format_checker=FormatChecker()).validate(media["example"])
            if path not in ("/api/v1/auth/login", "/api/v1/orcamentos/publico"):
                assert operation["security"] == [{"BearerAuth": []}]
    assert count == 14
    exported = json.loads((Path(__file__).resolve().parents[3] / "docs/openapi-v2.json").read_text(encoding="utf-8"))
    assert spec == exported
    assert client.get("/openapi.json").status_code == 200


def test_runtime_responses_match_contract_including_utc(client, app, accounts, contact, cargo):
    components = app.openapi()["components"]
    def valid(name, payload):
        Draft202012Validator({"$ref":"#/components/schemas/" + name,"components":components}, format_checker=FormatChecker()).validate(payload)
    headers = accounts["ADMIN"]["headers"]
    person = client.post("/api/v1/clientes", json=contact, headers=headers).json()
    valid("Cliente", person)
    valid("Cliente", client.get("/api/v1/clientes/" + person["id"], headers=headers).json())
    order = client.post("/api/v1/solicitacoes-orcamento", json={**cargo,"clienteId":person["id"]}, headers=headers).json()
    valid("SolicitacaoOrcamento", order)
    valid("SolicitacaoOrcamento", client.get("/api/v1/solicitacoes-orcamento/" + order["id"], headers=headers).json())
    valid("ListaClientes", client.get("/api/v1/clientes", headers=headers).json())
    valid("ListaSolicitacoes", client.get("/api/v1/solicitacoes-orcamento", headers=headers).json())
