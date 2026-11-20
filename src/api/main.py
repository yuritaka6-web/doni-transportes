import asyncio
import os
import secrets
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from .database import create_database, initialize
from .exceptions import install_handlers, problem
from .notifications import MailTransport, flush
from .routers import auth, clientes, solicitacoes
from .schemas import ApiError

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT
PUBLIC_FILES = {"index.html", "sobre.html", "servicos.html", "orcamento.html", "orcamento.js", "orcamento.css", "contato.js", "admin.html", "admin.js", "branding.css", "logo-doni.jpeg", "logo-doni-transparente.png", "caminhao2.jpeg", "caminhaobau.jpeg", "caminhaofrentepla.jpeg", "caminhaolado.jpeg"}
load_dotenv(SITE / ".env", override=False)


def create_app(database_url=None, jwt_secret=None, transport=None, scheduler=True):
    secret = jwt_secret or os.getenv("JWT_SECRET")
    production = os.getenv("ENVIRONMENT") == "production"
    if production and (not secret or len(secret) < 32):
        raise RuntimeError("Configure JWT_SECRET com pelo menos 32 caracteres.")
    engine, sessions = create_database(database_url)

    @asynccontextmanager
    async def lifespan(app):
        initialize(engine)
        async def worker():
            while True:
                try:
                    await asyncio.to_thread(flush, sessions, app.state.mail)
                except Exception:
                    pass  # A fila permanece persistida; não expor dados de contato nos logs.
                await asyncio.sleep(30)
        task = asyncio.create_task(worker()) if scheduler else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        engine.dispose()

    errors = {code: {"model": ApiError, "description": description} for code, description in {400:"Requisição inválida", 401:"JWT ausente/inválido", 403:"Perfil sem permissão", 404:"Recurso não encontrado", 409:"Conflito de relacionamento", 422:"Validação", 429:"Limite excedido", 503:"Serviço em configuração"}.items()}
    app = FastAPI(title="Doni Transportes — API de Orçamentos", version="2.0.0", description="API REST de clientes e solicitações de transporte. FastAPI, Pydantic v2, SQLAlchemy 2.0 e JWT/RBAC. Autoria: Yuri Vinicius Decaris Trevelin, RA 2840482321012.", lifespan=lifespan, responses=errors)
    app.state.engine, app.state.sessions = engine, sessions
    app.state.jwt_secret = secret or secrets.token_urlsafe(48)
    app.state.proxy_secret = os.getenv("PROXY_SECRET", "")
    app.state.mail = transport or MailTransport()
    install_handlers(app)

    @app.middleware("http")
    async def request_policy(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            origin = request.headers.get("origin")
            allowed = {"https://donitransportes.com.br", "https://www.donitransportes.com.br", str(request.base_url).rstrip("/")}
            if origin and origin not in allowed and request.method not in ("GET", "HEAD"):
                return problem(request, 403, "Origem não permitida.")
            allowed_query = {"pagina", "limite", "busca"} if request.url.path == "/api/v1/clientes" else {"pagina", "limite", "status", "clienteId"} if request.url.path == "/api/v1/solicitacoes-orcamento" else set()
            if request.url.path.startswith("/api/v1/clientes/") and request.url.path.endswith("/solicitacoes-orcamento"):
                allowed_query = {"pagina", "limite"}
            for key in request.query_params:
                if key not in allowed_query or len(request.query_params.getlist(key)) != 1:
                    return problem(request, 400, "Parâmetro desconhecido ou repetido.", [{"name": key, "reason": "Parâmetro não permitido nesta rota."}])
            if request.method in ("POST", "PATCH", "PUT"):
                if request.headers.get("content-type", "").split(";")[0].lower() != "application/json":
                    return problem(request, 415, "Use Content-Type application/json.")
                size = 0
                chunks = []
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 65536:
                        return problem(request, 413, "O corpo excede 64 KiB.")
                    chunks.append(chunk)
                request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(auth.router)
    app.include_router(clientes.router)
    app.include_router(solicitacoes.router)
    from .contract import documented_openapi
    app.openapi = lambda: documented_openapi(app)

    @app.get("/health", include_in_schema=False)
    def health():
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "version": "2.0.0"}

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(SITE / "index.html")

    @app.get("/{file}", include_in_schema=False)
    def asset(file: str):
        if file not in PUBLIC_FILES:
            from .exceptions import ApiFailure
            raise ApiFailure(404, "Arquivo não encontrado.")
        return FileResponse(SITE / file)

    return app


app = create_app()
