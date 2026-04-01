"""
Rotas de autenticação
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas import LoginRequest, TokenResponse
from app.auth import authenticate_user, create_access_token, get_current_user
from app.config import settings
from app.database import get_db
from app.utils import log_audit
from app.client_ip import get_client_ip

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Perfil do usuário autenticado (para o painel ocultar itens por perfil)."""
    return {
        "username": current_user.get("username"),
        "role": current_user.get("role"),
    }

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
_failed_attempts: dict[str, list[datetime]] = defaultdict(list)


def _check_brute_force(ip: str):
    """Bloqueia IP após muitas tentativas falhas de login"""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=LOCKOUT_MINUTES)

    _failed_attempts[ip] = [t for t in _failed_attempts[ip] if t > cutoff]

    if len(_failed_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
        logger.warning(f"IP bloqueado por brute force: {ip} ({len(_failed_attempts[ip])} tentativas)")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em alguns minutos."
        )


def _record_failed_attempt(ip: str):
    """Registra tentativa falha de login"""
    _failed_attempts[ip].append(datetime.utcnow())


def _clear_failed_attempts(ip: str):
    """Limpa tentativas falhas após login bem-sucedido"""
    _failed_attempts.pop(ip, None)


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Encerra a sessão do administrador"""
    log_audit(db, "logout", "auth", ip=get_client_ip(request))
    response = JSONResponse(content={"ok": True})
    response.delete_cookie("admin_token")
    return response


@router.post("/login")
async def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Endpoint de login
    Retorna token JWT para autenticação e define cookie
    """
    ip = get_client_ip(request)

    _check_brute_force(ip)

    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        _record_failed_attempt(ip)
        remaining = MAX_LOGIN_ATTEMPTS - len(_failed_attempts[ip])
        log_audit(db, "login_failed", "auth", f"Tentativa com usuário: {credentials.username} (restam {remaining})", ip=ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_failed_attempts(ip)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    log_audit(db, "login_success", "auth", user=user.username, ip=ip)

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "role": user.role,
        }
    )

    response.set_cookie(
        key="admin_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG
    )

    return response

