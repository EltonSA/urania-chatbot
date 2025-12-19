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
    """Endpoint raiz"""
    return {
        "message": "SaaS Chatbot com PDFs e GIFs está rodando.",
        "version": "1.0.0",
        "admin": "/admin",
        "widget": "/widget",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "login": "/login"
    }

