"""
Rotas para páginas HTML
"""
import os
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from app.config import settings

router = APIRouter(tags=["Páginas"])
security = HTTPBearer(auto_error=False)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def verify_token_from_cookie_or_header(request: Request, token: str = None) -> bool:
    """Verifica token JWT de cookie ou header"""
    # Tenta pegar do cookie primeiro
    token = request.cookies.get("admin_token") or token
    
    # Se não tiver no cookie, tenta no header Authorization
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if not token:
        return False
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub") is not None
    except JWTError:
        return False


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    """Página de administração - Requer autenticação"""
    if not verify_token_from_cookie_or_header(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse(os.path.join(BASE_DIR, "admin.html"))


@router.get("/widget", response_class=HTMLResponse)
def widget_page():
    """Página do widget de chat - Pública"""
    return FileResponse(os.path.join(BASE_DIR, "widget.html"))


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    """Página do dashboard - Requer autenticação"""
    if not verify_token_from_cookie_or_header(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse(os.path.join(BASE_DIR, "dashboard.html"))


@router.get("/login", response_class=HTMLResponse)
def login_page():
    """Página de login"""
    return FileResponse(os.path.join(BASE_DIR, "login.html"))


@router.get("/")
def root():
    """
    Endpoint raiz
    
    Comportamento:
    - Em produção (DEBUG=False): redireciona para /widget por padrão
    - Em desenvolvimento (DEBUG=True): retorna JSON com informações por padrão
    - Pode ser configurado via ROOT_REDIRECT no .env:
      * "widget" -> redireciona para /widget
      * "admin" -> redireciona para /admin
      * "dashboard" -> redireciona para /dashboard
      * "login" -> redireciona para /login
      * "json" -> retorna JSON (apenas em desenvolvimento)
      * vazio -> usa padrão baseado em DEBUG
    """
    # Determina o comportamento baseado na configuração
    redirect_target = settings.ROOT_REDIRECT
    
    # Se não estiver configurado, usa padrão baseado em DEBUG
    if not redirect_target:
        if settings.DEBUG:
            # Em desenvolvimento, retorna JSON
            redirect_target = "json"
        else:
            # Em produção, redireciona para widget
            redirect_target = "widget"
    
    # Executa redirecionamento ou retorna JSON
    if redirect_target == "json":
        # Apenas em desenvolvimento
        if not settings.DEBUG:
            # Em produção, força redirecionamento para widget mesmo se configurado como json
            return RedirectResponse(url="/widget", status_code=status.HTTP_302_FOUND)
        
        return {
            "message": f"{settings.APP_NAME} está rodando.",
            "version": settings.APP_VERSION,
            "admin": "/admin",
            "widget": "/widget",
            "dashboard": "/dashboard",
            "docs": "/docs" if settings.DEBUG else None,
            "login": "/login"
        }
    elif redirect_target == "widget":
        return RedirectResponse(url="/widget", status_code=status.HTTP_302_FOUND)
    elif redirect_target == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    elif redirect_target == "dashboard":
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    elif redirect_target == "login":
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    else:
        # Valor inválido, usa padrão (widget em produção)
        if settings.DEBUG:
            return {
                "message": f"{settings.APP_NAME} está rodando.",
                "version": settings.APP_VERSION,
                "admin": "/admin",
                "widget": "/widget",
                "dashboard": "/dashboard",
                "docs": "/docs",
                "login": "/login"
            }
        else:
            return RedirectResponse(url="/widget", status_code=status.HTTP_302_FOUND)

