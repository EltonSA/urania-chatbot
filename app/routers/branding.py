"""
Marca pública: nome exibido e favicon (sem autenticação).
"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.utils import (
    get_setting,
    resolve_branding_favicon,
    branding_favicon_cache_bust,
    resolve_branding_logo,
    branding_logo_cache_bust,
    resolve_effective_chat_avatar,
    branding_chat_avatar_cache_bust,
    LOGO_STATIC_PATH,
)

router = APIRouter(tags=["Branding"])


@router.get("/branding")
def public_branding(db: Session = Depends(get_db)):
    """Nome, favicon, logos e versão para páginas e widget."""
    raw = (get_setting(db, "system_display_name") or "").strip()
    display_name = raw if raw else settings.APP_NAME
    path, _ = resolve_branding_favicon()
    if path:
        v = branding_favicon_cache_bust()
        favicon_url = f"/branding/favicon?v={v}"
    else:
        favicon_url = "/static/favicon.ico"

    lp, _ = resolve_branding_logo()
    if lp:
        logo_url = f"/branding/logo?v={branding_logo_cache_bust()}"
    else:
        logo_url = LOGO_STATIC_PATH

    cap, _ = resolve_effective_chat_avatar()
    if cap:
        chat_avatar_url = f"/branding/chat-avatar?v={branding_chat_avatar_cache_bust()}"
    else:
        chat_avatar_url = LOGO_STATIC_PATH

    return {
        "display_name": display_name,
        "favicon_url": favicon_url,
        "logo_url": logo_url,
        "chat_avatar_url": chat_avatar_url,
        "version": settings.resolved_app_version,
    }


@router.get("/branding/favicon")
def public_branding_favicon():
    """Serve o favicon personalizado ou redireciona para o estático padrão."""
    path, media_type = resolve_branding_favicon()
    if path and media_type:
        return FileResponse(path, media_type=media_type)
    return RedirectResponse(url="/static/favicon.ico", status_code=302)


@router.get("/branding/logo")
def public_branding_logo():
    """Logo do painel (sidebar, login) ou redireciona para o estático padrão."""
    path, media_type = resolve_branding_logo()
    if path and media_type:
        return FileResponse(path, media_type=media_type)
    return RedirectResponse(url=LOGO_STATIC_PATH, status_code=302)


@router.get("/branding/chat-avatar")
def public_branding_chat_avatar():
    """Avatar do assistente no chat: chat-avatar.*, senão logo.*, senão estático."""
    path, media_type = resolve_effective_chat_avatar()
    if path and media_type:
        return FileResponse(path, media_type=media_type)
    return RedirectResponse(url=LOGO_STATIC_PATH, status_code=302)
