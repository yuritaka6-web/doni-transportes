import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from .database import get_db
from .exceptions import ApiFailure
from .models import UserModel, RateLimitModel

bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")
ISSUER = "doni-transportes"
AUDIENCE = "doni-api"


def hash_password(password: str):
    salt = secrets.token_hex(16)
    value = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64)
    return f"scrypt${salt}${value.hex()}"


def verify_password(password, encoded):
    try:
        kind, salt, expected = encoded.split("$")
        if kind != "scrypt" or len(salt) != 32 or len(expected) != 128:
            return False
        actual = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def make_token(user, secret, expires=3600):
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": user.id, "email": user.email, "role": user.role, "iat": now, "exp": now + timedelta(seconds=expires), "iss": ISSUER, "aud": AUDIENCE, "jti": secrets.token_hex(16)}, secret, algorithm="HS256")


def get_current_user(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db=Depends(get_db)):
    try:
        if credentials is None:
            raise ValueError()
        payload = jwt.decode(credentials.credentials, request.app.state.jwt_secret, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE, options={"require": ["sub", "email", "role", "iat", "exp", "iss", "aud", "jti"]})
        user = db.get(UserModel, payload["sub"])
        if not user or user.email != payload["email"] or user.role != payload["role"]:
            raise ValueError()
        return user
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise ApiFailure(401, "Token ausente, inválido ou expirado.", headers={"WWW-Authenticate": "Bearer"}) from None


def require_roles(*roles):
    def authorize(user=Depends(get_current_user)):
        if user.role not in roles:
            raise ApiFailure(403, "Seu perfil não permite esta operação.")
        return user
    return authorize


def enforce_limit(request: Request, db, kind, maximum, seconds):
    # O proxy só encaminha IP autenticado por chave privada; clientes diretos não podem forjar X-Forwarded-For.
    trusted = request.app.state.proxy_secret and hmac.compare_digest(request.headers.get("x-doni-proxy-key", ""), request.app.state.proxy_secret)
    ip = request.headers.get("x-doni-client-ip", "") if trusted else (request.client.host if request.client else "unknown")
    window = int(time.time()) // seconds
    key = f"{kind}:{hashlib.sha256(ip.encode()).hexdigest()}:{window}"
    insert = postgres_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    stmt = insert(RateLimitModel).values(chave=key, quantidade=1, expira_em=int(time.time()) + seconds)
    stmt = stmt.on_conflict_do_update(index_elements=[RateLimitModel.chave], set_={"quantidade": RateLimitModel.quantidade + 1}).returning(RateLimitModel.quantidade)
    amount = db.execute(stmt).scalar_one()
    db.commit()
    if amount > maximum:
        raise ApiFailure(429, "Muitas tentativas. Tente novamente mais tarde.", headers={"Retry-After": str(seconds - int(time.time()) % seconds)})
