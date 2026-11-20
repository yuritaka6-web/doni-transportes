from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse

TITLES = {400: ("bad-request", "Requisição inválida"), 401: ("unauthorized", "Autenticação necessária"), 403: ("forbidden", "Acesso negado"), 404: ("not-found", "Recurso não encontrado"), 405: ("method-not-allowed", "Método não permitido"), 409: ("conflict", "Conflito"), 413: ("payload-too-large", "Conteúdo muito grande"), 415: ("unsupported-media-type", "Tipo de conteúdo inválido"), 422: ("validation-error", "Dados inválidos"), 429: ("too-many-requests", "Limite excedido"), 500: ("internal-error", "Falha interna"), 503: ("service-unavailable", "Serviço indisponível")}


class ApiFailure(Exception):
    def __init__(self, status, detail, invalid=None, headers=None):
        self.status, self.detail, self.invalid, self.headers = status, detail, invalid or [], headers or {}


def problem(request, status, detail, invalid=None, headers=None):
    slug, title = TITLES.get(status, TITLES[500])
    return JSONResponse(status_code=status, media_type="application/problem+json", headers={"Cache-Control": "no-store", **(headers or {})}, content={"type": f"https://donitransportes.com.br/problems/{slug}", "title": title, "status": status, "detail": detail, "instance": request.url.path, "invalidParams": invalid or []})


def install_handlers(app):
    @app.exception_handler(ApiFailure)
    async def failure(request: Request, exc: ApiFailure):
        return problem(request, exc.status, exc.detail, exc.invalid, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation(request: Request, exc: RequestValidationError):
        invalid = [{"name": "/".join(str(x) for x in error["loc"] if x not in ("body", "query", "path")), "reason": error["msg"]} for error in exc.errors()]
        status = 400 if any(e["type"] == "json_invalid" or e["loc"][0] in ("query", "path") for e in exc.errors()) else 422
        return problem(request, status, "Confira os campos informados.", invalid)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return problem(request, exc.status_code, str(exc.detail), headers=exc.headers)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        # Nunca inserir exceções SQL/SMTP, dados de formulário ou segredos na resposta.
        return problem(request, 500, "Não foi possível concluir a operação.")
