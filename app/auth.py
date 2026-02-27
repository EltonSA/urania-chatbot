"""
Sistema de autenticação
"""
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import SessionLocal
from app.utils import get_setting, set_setting

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Gera hash bcrypt da senha"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
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


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """
    Verifica e decodifica o token JWT
    Retorna os dados do token se válido
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except JWTError as e:
        logger.warning(f"Falha na verificação do token JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str) -> bool:
    """
    Autentica usuário usando bcrypt.
    O hash da senha é armazenado no banco (chave admin_password_hash).
    Se o .env mudar a senha, o hash é regenerado no próximo startup.
    """
    if username != settings.ADMIN_USERNAME:
        return False

    db = SessionLocal()
    try:
        stored_hash = get_setting(db, "admin_password_hash")
        if not stored_hash:
            stored_hash = _initialize_password_hash(db)

        return verify_password(password, stored_hash)
    except Exception as e:
        logger.error(f"Erro na autenticação: {e}")
        return False
    finally:
        db.close()


def _initialize_password_hash(db) -> str:
    """Gera e armazena o hash inicial da senha admin"""
    hashed = get_password_hash(settings.ADMIN_PASSWORD)
    set_setting(db, "admin_password_hash", hashed)
    logger.info("Hash bcrypt da senha admin gerado e armazenado")
    return hashed


def get_current_user(token_data: dict = Depends(verify_token)) -> dict:
    """
    Dependency para obter usuário atual autenticado
    """
    return token_data

