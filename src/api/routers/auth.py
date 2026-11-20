from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from ..database import get_db
from ..exceptions import ApiFailure
from ..models import UserModel
from ..schemas import LoginRequestDTO, TokenResponseDTO, UserResponse
from ..security import enforce_limit, get_current_user, make_token, verify_password
from ..views import user_view

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponseDTO, summary="Autenticar operador")
def login(data: LoginRequestDTO, request: Request, db=Depends(get_db)):
    enforce_limit(request, db, "login", 5, 900)
    user = db.scalar(select(UserModel).where(UserModel.email == data.email.lower()))
    dummy = "scrypt$" + "0" * 32 + "$" + "0" * 128
    valid = verify_password(data.password, user.password_hash if user else dummy)
    if not user or not valid:
        raise ApiFailure(401, "E-mail ou senha inválidos.", headers={"WWW-Authenticate": "Bearer"})
    return {"accessToken": make_token(user, request.app.state.jwt_secret), "tokenType": "bearer", "expiresIn": 3600, "user": user_view(user)}


@router.get("/me", response_model=UserResponse, summary="Consultar operador autenticado")
def me(user=Depends(get_current_user)):
    return user_view(user)
