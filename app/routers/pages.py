"""
Rotas para páginas HTML
"""
import os
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.utils import get_setting

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
    """Página do widget de chat - Pública (com proteção frame-ancestors)"""
    file_path = os.path.join(BASE_DIR, "widget.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    allowed = settings.widget_allowed_origins_list
    if allowed:
        csp = "frame-ancestors 'self' " + " ".join(allowed)
    else:
        csp = "frame-ancestors *"
    
    return HTMLResponse(
        content=content,
        headers={"Content-Security-Policy": csp}
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    """Página do dashboard - Requer autenticação"""
    if not verify_token_from_cookie_or_header(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse(os.path.join(BASE_DIR, "dashboard.html"))


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    """Página de configurações do sistema - Requer autenticação"""
    if not verify_token_from_cookie_or_header(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse(os.path.join(BASE_DIR, "settings.html"))


@router.get("/login", response_class=HTMLResponse)
def login_page():
    """Página de login"""
    return FileResponse(os.path.join(BASE_DIR, "login.html"))


@router.get("/conversations", response_class=HTMLResponse)
def conversations_page(request: Request):
    """Página de conversas - Requer autenticação"""
    if not verify_token_from_cookie_or_header(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse(os.path.join(BASE_DIR, "conversations.html"))


@router.get("/conversation-view.html", response_class=HTMLResponse)
def conversation_view_page(request: Request):
    """Página de visualização de conversa - Requer autenticação"""
    if not verify_token_from_cookie_or_header(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return FileResponse(os.path.join(BASE_DIR, "conversation-view.html"))


def _is_safe_redirect(url: str) -> bool:
    """Aceita URLs relativas (/) ou absolutas (http/https). Rejeita javascript: e //"""
    if not url or not url.strip():
        return False
    url = url.strip()
    if url.startswith("//") or url.lower().startswith("javascript:"):
        return False
    if url.startswith("/"):
        return True
    if url.lower().startswith("https://") or url.lower().startswith("http://"):
        return True
    return False


@router.get("/")
def root(db: Session = Depends(get_db)):
    """
    Endpoint raiz - comportamento configurável via painel de configurações.
    Opções: blank (página em branco), widget (redireciona para chat), custom (URL relativa).
    """
    behavior = get_setting(db, "root_behavior") or "widget"

    if behavior == "blank":
        return HTMLResponse(content="", status_code=200)
    elif behavior == "custom":
        custom_url = (get_setting(db, "root_custom_url") or "").strip()
        if custom_url and _is_safe_redirect(custom_url):
            return RedirectResponse(url=custom_url, status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/widget", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="/widget", status_code=status.HTTP_302_FOUND)

