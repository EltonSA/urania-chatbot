"""
Rotas de autenticação
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from app.schemas import LoginRequest, TokenResponse
from app.auth import authenticate_user, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login")
async def login(credentials: LoginRequest):
    """
    Endpoint de login
    Retorna token JWT para autenticação e define cookie
    """
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": credentials.username},
        expires_delta=access_token_expires
    )
    
    # Cria resposta JSON com o token
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer"
        }
    )
    
    # Define cookie com o token para verificação nas páginas HTML
    response.set_cookie(
        key="admin_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=False  # Mude para True em produção com HTTPS
    )
    
    return response

