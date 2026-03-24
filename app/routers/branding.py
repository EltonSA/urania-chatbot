"""
Marca pública: nome exibido e favicon (sem autenticação).
"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.utils import get_setting, resolve_branding_favicon, branding_favicon_cache_bust

router = APIRouter(tags=["Branding"])


@router.get("/branding")
def public_branding(db: Session = Depends(get_db)):
    """Nome e URL do favicon para páginas e widget flutuante."""
    raw = (get_setting(db, "system_display_name") or "").strip()
    display_name = raw if raw else settings.APP_NAME
    path, _ = resolve_branding_favicon()
    if path:
        v = branding_favicon_cache_bust()
        favicon_url = f"/branding/favicon?v={v}"
    else:
        favicon_url = "/static/favicon.ico"
    return {
        "display_name": display_name,
        "favicon_url": favicon_url,
        "version": settings.resolved_app_version,
    }


@router.get("/branding/favicon")
def public_branding_favicon():
    """Serve o favicon personalizado ou redireciona para o estático padrão."""
    path, media_type = resolve_branding_favicon()
    if path and media_type:
        return FileResponse(path, media_type=media_type)
    return RedirectResponse(url="/static/favicon.ico", status_code=302)
