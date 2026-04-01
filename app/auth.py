"""
Sistema de autenticação
"""
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import UserModel

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

ROLE_ADMIN = "admin"
ROLE_USER = "user"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Gera hash bcrypt da senha"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user_from_token_string(db: Session, token: str) -> Optional[UserModel]:
    """Resolve usuário a partir do JWT (sub = username)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        return db.query(UserModel).filter(UserModel.username == username).first()
    except JWTError as e:
        logger.warning("Falha na verificação do token JWT: %s", e)
        return None


def verify_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    Verifica JWT (header Bearer ou cookie admin_token) e retorna dados do usuário no banco.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None
    if credentials:
        token = credentials.credentials
    if not token:
        token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_from_token_string(db, token)
    if not user:
        raise credentials_exception

    return {"username": user.username, "role": user.role, "sub": user.username}


def get_user_from_request_cookie_or_bearer(request: Request, db: Session) -> Optional[UserModel]:
    """Para rotas HTML: token em cookie ou Authorization."""
    token = request.cookies.get("admin_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
    if not token:
        return None
    return get_user_from_token_string(db, token)


def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
    """Autentica por usuário/senha no banco."""
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return None
    if verify_password(password, user.password_hash):
        return user
    return None


def get_current_user(token_data: dict = Depends(verify_token)) -> dict:
    """Dependency: usuário autenticado (qualquer role)."""
    return token_data


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: apenas administrador."""
    if current_user.get("role") != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user
